"""Map structural message/event envelopes into a producer-neutral event stream."""

from model_trace_common import canonical

KINDS = {'user_message', 'assistant_message', 'system_message', 'tool_call', 'tool_result',
         'reasoning', 'error', 'metric', 'artifact', 'session_start', 'session_end', 'unknown'}
ROLES = {'user': 'user_message', 'assistant': 'assistant_message', 'system': 'system_message',
         'developer': 'system_message', 'tool': 'tool_result'}
CALLS = {'tool_use', 'tool_call', 'function_call', 'custom_tool_call'}
RESULTS = {'tool_result', 'function_call_output', 'custom_tool_call_output'}
EXIT_KEYS = ('exit', 'exit_code', 'exitCode', 'returncode', 'return_code', 'returnCode')
TRUNCATED_KEYS = ('truncated', 'is_truncated', 'output_truncated', 'outputTruncated')


def execution_evidence(event, source):
    """Keep result metadata and distinguish process outcomes from lifecycle completion."""
    fields = {*EXIT_KEYS, *TRUNCATED_KEYS, 'status', 'metadata', 'time', 'outcome', 'result_metadata', 'limitations'}
    preserved = {key: value for key, value in source.items() if key in fields}
    if not preserved:
        return event
    event['result_metadata'] = preserved
    locations = [source, *(value for key, value in preserved.items()
                           if key in {'metadata', 'outcome', 'result_metadata'} and isinstance(value, dict))]
    exits = [obj[key] for obj in locations for key in EXIT_KEYS if key in obj]
    truncated = [obj[key] for obj in locations for key in TRUNCATED_KEYS if key in obj]
    limitations = list(event.get('limitations', []))
    if isinstance(source.get('limitations'), list):
        limitations.extend(item for item in source['limitations'] if isinstance(item, str))
    outcome = {}
    if exits:
        if all(type(code) is int for code in exits) and len(set(exits)) == 1:
            outcome['exit_code'] = exits[0]
            if exits[0] != 0:
                outcome['failed'] = True
                event['event_type'] = 'error'
        else:
            limitations.append('ambiguous_exit_status')
    if truncated:
        if all(type(value) is bool for value in truncated):
            outcome['output_truncated'] = any(truncated)
            if any(truncated):
                limitations.append('tool_output_truncated')
        else:
            limitations.append('ambiguous_output_completeness')
    status = source.get('status')
    if status is not None:
        outcome['lifecycle'] = status
        if isinstance(status, str) and status in {'error', 'failed', 'cancelled', 'canceled', 'aborted', 'timeout', 'timed_out'}:
            outcome['failed'] = True
            event['event_type'] = 'error'
        elif not isinstance(status, str) or status not in {'completed', 'success', 'succeeded', 'running', 'pending'}:
            limitations.append('unrecognized_tool_status')
            event['event_type'] = 'unknown'
    if outcome:
        event['outcome'] = outcome
    if limitations:
        event['limitations'] = sorted(set(limitations))
        if any(item.startswith('ambiguous_') for item in limitations):
            event['event_type'] = 'unknown'
    return event


def text(value):
    return value if isinstance(value, str) else canonical(value).decode() if value is not None else ''


def get_path(value, path):
    for key in path.split('.'):
        if isinstance(value, list) and key.isdecimal() and int(key) < len(value):
            value = value[int(key)]
            continue
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


class Adapter:
    def __init__(self, session, mapping=None):
        self.context = {'session_id': session, 'parent_session_id': None, 'timestamp': None}
        self.mapping = mapping
        self.snapshot_histories = {}
        self.warnings = []

    def snapshot(self, value, mapping=None):
        """Remove inherited prefixes by position, retaining genuine identical turns."""
        mapping = mapping or {}
        if not isinstance(value, dict):
            yield self.event('unknown', 'unknown', value, self.context, '$')
            return
        messages_path = mapping.get('messages_path', 'messages')
        messages = get_path(value, messages_path)
        session = get_path(value, mapping['session_id']) if mapping.get('session_id') else value.get('session_id')
        ctx = {'session_id': session if session is not None else self.context['session_id'],
               'parent_session_id': get_path(value, mapping['parent_session_id'])
               if mapping.get('parent_session_id') else value.get('parent_session_id'), 'timestamp': None}
        if not isinstance(messages, list):
            self.warnings.append('Snapshot messages missing; original record retained as unknown.')
            yield self.event('unknown', 'unknown', value, ctx, '$')
            return
        items = [(message, '$.' + messages_path + f'[{i}]') for i, message in enumerate(messages)]
        response = get_path(value, mapping['response_path']) if mapping.get('response_path') else None
        # Wire formats such as undecoded SSE remain unknown; never manufacture a completed message.
        response_message = isinstance(response, dict) and (
            'role' in response or 'event_type' in response or isinstance(response.get('message'), dict))
        if response_message:
            items.append((response, '$.' + mapping['response_path']))
        history = [canonical(message) for message, _ in items]
        key = canonical(ctx['session_id'])
        previous = self.snapshot_histories.get(key, [])
        if len(history) < len(previous) or history[:len(previous)] != previous:
            self.warnings.append('Non-prefix or shorter snapshot retained as unknown; branch order not inferred.')
            yield self.event('unknown', 'unknown', value, ctx, '$')
            return
        for message, locator in items[len(previous):]:
            yield from self.convert(message, locator, ctx)
        self.snapshot_histories[key] = history
        if response is not None and not response_message:
            self.warnings.append('Undecoded snapshot response retained as unknown.')
            yield self.event('unknown', 'unknown', response, ctx, '$.' + mapping['response_path'])

    def convert(self, value, locator='$', context=None):
        ctx = dict(context or self.context)
        if isinstance(value, list):
            for index, item in enumerate(value):
                yield from self.convert(item, f'{locator}[{index}]', ctx)
            return
        if not isinstance(value, dict):
            yield self.event('unknown', 'unknown', value, ctx, locator)
            return
        if self.mapping is not None:
            fields = {key: get_path(value, path) for key, path in self.mapping['fields'].items()}
            kind = fields.get('event_type')
            kind = self.mapping.get('event_types', {}).get(kind, kind) if isinstance(kind, str) else None
            ctx.update({key: fields[key] for key in ('session_id', 'parent_session_id', 'timestamp')
                        if fields.get(key) is not None})
            if kind not in KINDS or fields.get('text') is None:
                yield self.event('unknown', 'unknown', value, ctx, locator)
            else:
                event = self.event(kind, fields.get('actor') or 'unknown', fields['text'], ctx, locator,
                                   fields.get('tool_name'), fields.get('call_id'))
                yield execution_evidence(event, fields) if kind in {'tool_result', 'error'} else event
            return
        info = value.get('info') if isinstance(value.get('info'), dict) else {}
        session = value.get('session') if isinstance(value.get('session'), dict) else None
        if session is not None:
            ctx['session_id'] = session.get('id', session.get('session_id', ctx['session_id']))
            ctx['parent_session_id'] = session.get('parent_session_id', session.get('parentID'))
        if isinstance(value.get('type'), str) and value['type'] in {'session.created', 'session.updated'}:
            properties = value.get('properties') or {}
            declared = properties.get('info') if isinstance(properties, dict) else None
            if isinstance(declared, dict):
                ctx.update(session_id=declared.get('id', ctx['session_id']),
                           parent_session_id=declared.get('parent_session_id', declared.get('parentID')))
                self.context = {key: ctx[key] for key in ('session_id', 'parent_session_id', 'timestamp')}
                yield self.event('session_start', 'system', declared, ctx, locator + '.properties.info')
                return
        for key, aliases in {'session_id': ('session_id', 'sessionId', 'sessionID'),
                             'parent_session_id': ('parent_session_id', 'parentSessionId', 'parentSessionID'),
                             'timestamp': ('timestamp',)}.items():
            for alias in aliases:
                candidate = value.get(alias, info.get(alias))
                if candidate is not None:
                    if key == 'session_id' and candidate != ctx[key]:
                        ctx['parent_session_id'] = None
                    ctx[key] = candidate
                    break
        self.context = {key: ctx[key] for key in ('session_id', 'parent_session_id', 'timestamp')}
        self.context['timestamp'] = None
        if isinstance(value.get('role', info.get('role')), str) and value.get('role', info.get('role')) in ROLES:
            for key, aliases in {'message_id': ('id',), 'parent_message_id': ('parentID', 'parent_message_id')}.items():
                for alias in aliases:
                    identifier = value.get(alias, info.get(alias))
                    if identifier is not None:
                        ctx[key] = identifier
                        break
        kind = value.get('type')
        kind = kind if isinstance(kind, str) else None
        payload = value.get('payload')
        if kind == 'session_meta' and isinstance(payload, dict):
            ctx['session_id'] = payload.get('id') or ctx['session_id']
            ctx['parent_session_id'] = payload.get('parent_session_id', ctx['parent_session_id'])
            self.context = {**ctx, 'timestamp': None}
            yield self.event('session_start', 'system', payload, ctx, locator + '.payload')
            return
        if kind in {'response_item', 'event_msg'} and isinstance(payload, dict):
            yield from self.convert(payload, locator + '.payload', ctx)
            return
        for container in ('messages', 'events'):
            if isinstance(value.get(container), list):
                yield from self.convert(value[container], locator + '.' + container, ctx)
                return
        if isinstance(value.get('message'), dict):
            message = value['message']
            message = {'role': value.get('role', kind), **message}
            yield from self.convert(message, locator + '.message', ctx)
            return
        explicit = value.get('event_type')
        explicit = explicit if isinstance(explicit, str) else None
        if explicit in KINDS:
            body = value.get('content', value.get('text', ''))
            if isinstance(body, dict) and 'text' in body:
                body = body['text']
            tool = value.get('tool') if isinstance(value.get('tool'), dict) else {}
            event = self.event(explicit, value.get('actor', 'unknown'), body, ctx, locator,
                               tool.get('name'), tool.get('call_id'))
            yield execution_evidence(event, value) if explicit in {'tool_result', 'error'} else event
            return
        if kind in CALLS:
            yield self.event('tool_call', 'assistant', value.get('arguments', value.get('input')), ctx,
                             locator, value.get('name'), value.get('call_id', value.get('id')))
            return
        if kind in RESULTS:
            result_kind = 'error' if value.get('is_error') is True else 'tool_result'
            yield execution_evidence(self.event(result_kind, 'tool', value.get('output', value.get('content')), ctx,
                                     locator, value.get('name'), value.get('call_id', value.get('tool_use_id'))), value)
            return
        role = value.get('role', info.get('role'))
        role = role if isinstance(role, str) else None
        if kind in ROLES and role is None:
            role = kind
        if kind in {'user_message', 'assistant_message', 'agent_message'} and role is None:
            role = 'user' if kind == 'user_message' else 'assistant'
        if kind in {'reasoning', 'thinking'}:
            yield self.event('reasoning', 'assistant', value.get('thinking', value.get('text', value)), ctx, locator)
            return
        if kind in {'error', 'metric', 'artifact'}:
            yield self.event(kind, role or 'unknown', value.get('text', value), ctx, locator)
            return
        if role not in ROLES:
            yield self.event('unknown', 'unknown', value, ctx, locator)
            return
        if 'tool_calls' in value and not isinstance(value['tool_calls'], list):
            yield self.event('unknown', 'unknown', value, ctx, locator)
            return
        content = value.get('parts', value.get('content', value.get('text', value.get('message'))))
        if isinstance(content, list):
            for index, block in enumerate(content):
                field = 'parts' if 'parts' in value else 'content'
                for item in self.block(block, role, ctx, f'{locator}.{field}[{index}]'):
                    if role == 'tool' and item['event_type'] == 'tool_result' and item['tool'] is None:
                        call_id = value.get('tool_call_id', value.get('call_id'))
                        name = value.get('name', info.get('tool'))
                        item['tool'] = {'name': name, 'call_id': call_id} if name is not None or call_id is not None else None
                    if role == 'tool' and item['event_type'] == 'tool_result' and value.get('is_error') is True:
                        item['event_type'] = 'error'
                    yield execution_evidence(item, value) if role == 'tool' else item
        elif content is not None:
            result_kind = 'error' if role == 'tool' and value.get('is_error') is True else ROLES[role]
            event = self.event(result_kind, role, content, ctx, locator, value.get('name', info.get('tool')),
                               value.get('tool_call_id', value.get('call_id')))
            yield execution_evidence(event, value) if role == 'tool' else event
        for index, call in enumerate(value.get('tool_calls', [])):
            if not isinstance(call, dict):
                yield self.event('unknown', 'unknown', call, ctx, f'{locator}.tool_calls[{index}]')
                continue
            function = call.get('function', call)
            if not isinstance(function, dict):
                yield self.event('unknown', 'unknown', call, ctx, f'{locator}.tool_calls[{index}]')
                continue
            yield self.event('tool_call', 'assistant', function.get('arguments', function.get('input')), ctx,
                             f'{locator}.tool_calls[{index}]', function.get('name'), call.get('id'))
        if content is None and not value.get('tool_calls'):
            yield self.event('unknown', 'unknown', value, ctx, locator)

    def block(self, block, role, ctx, locator):
        if not isinstance(block, dict):
            yield self.event('unknown', 'unknown', block, ctx, locator)
            return
        kind = block.get('type')
        kind = kind if isinstance(kind, str) else None
        if kind in {'text', 'input_text', 'output_text'}:
            yield self.event(ROLES[role], role, block.get('text', ''), ctx, locator)
        elif kind in CALLS | RESULTS | {'reasoning', 'thinking', 'error', 'metric', 'artifact'}:
            yield from self.convert(block, locator, ctx)
        elif kind == 'tool' and isinstance(block.get('state'), dict):
            state = block['state']
            yield self.event('tool_call', 'assistant', state.get('input'), ctx, locator,
                             block.get('tool'), block.get('callID'))
            if state.get('status') == 'completed' and 'output' in state:
                event = execution_evidence(self.event('tool_result', 'tool', state['output'], ctx, locator,
                                                     block.get('tool'), block.get('callID')), state)
                if event.get('limitations'):
                    self.warnings.extend(event['limitations'])
                yield event
            elif state.get('status') == 'error':
                yield execution_evidence(self.event('error', 'tool', state.get('error', state), ctx, locator,
                                                     block.get('tool'), block.get('callID')), state)
            else:
                self.warnings.append('unrecognized_or_incomplete_tool_state')
                event = self.event('unknown', 'unknown', block, ctx, locator, block.get('tool'), block.get('callID'))
                event['limitations'] = ['unrecognized_or_incomplete_tool_state']
                yield execution_evidence(event, state)
        else:
            yield self.event('unknown', 'unknown', block, ctx, locator)

    @staticmethod
    def event(kind, actor, value, context, locator, name=None, call_id=None):
        return {**context, 'schema_version': 'trace.event.v1', 'event_type': kind, 'actor': actor,
                'tool': {'name': name, 'call_id': call_id} if name is not None or call_id is not None else None,
                'content': {'text': text(value)}, 'locator': locator}
