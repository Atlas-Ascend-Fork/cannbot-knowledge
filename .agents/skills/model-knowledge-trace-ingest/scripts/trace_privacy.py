"""Generic, local redaction and safe publication findings; never execute trace data."""

from collections import Counter
import ipaddress
import json
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


PROFILE = 'agent.trace-redaction.v2'
SECRET_KEY = re.compile(r'(?i)(?:[a-z][a-z0-9_-]*[_-])?(?:password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|secret[_-]?key|access[_-]?key(?:_id)?|secret_access_key|ak|sk|authorization|cookie|set-cookie|密码|账号密码)$')
ASSIGNMENT = re.compile(
    r'(?i)((?<![\w-])(?:[A-Z][A-Z0-9_-]*[_-](?:AK|SK)|(?:[A-Z][A-Z0-9_-]*[_-])?(?:access_key_id|secret_access_key|api[_-]?key|access_token|refresh_token|password|passwd|secret|authorization|cookie|set-cookie)|token|账号密码|密码)["\']?[ \t]*[:=：][ \t]*)'
    r'("(?:\\.|[^"\\\r\n])*"|\'(?:\\.|[^\'\\\r\n])*\'|[^\s,;"\'<>]+)')
EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
IPV4 = re.compile(r'(?<![A-Za-z0-9_.])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9_]|\.[A-Za-z0-9_])')
PRIVATE_HOST = re.compile(r'(?i)(?<![A-Za-z0-9_.-])[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*\.(?:internal|intranet|corp|lan|local)(?![A-Za-z0-9_-]|\.[A-Za-z0-9_-])')
URL = re.compile(r'(?:https?|ssh|git)://(?:\[[^\]\s]+\]|[^\s<>"\')\[\]，。；：（）【】、“”‘’])+')
ROOT = r'(?:~/|/(?:home|Users|root|work|workspace|workspaces|data|mnt/workspace|mnt/data|tmp|var/tmp|(?:export|nfs|lustre)/(?:home|workspace))/|[A-Za-z]:[\\/]+(?:Users|workspace|workspaces)[\\/]+)'
PRIVATE_PATH = re.compile(r'(?<![A-Za-z0-9_}>/])' + ROOT + r'[^\s\x00-\x1f\'"`<>;,)|}\]，。；：（）【】、“”‘’]+')
QUOTED_PATH = re.compile(r'(["\'])(' + ROOT + r'[^\x00-\x1f"\']+)\1')
PATH_KEYS = {'path', 'cwd', 'workdir', 'directory', 'home', 'model_path', 'file', 'filename', 'output_path'}
VERSION_KEYS = {'version', 'release', 'build_version', 'cann_version', 'cuda_version', 'torch_version'}
NETWORKS = tuple(ipaddress.ip_network(value) for value in
                 ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '100.64.0.0/10', 'fc00::/7', 'fe80::/10'])
INTERNAL_REFERENCE = re.compile(r'见\s*候选(?:\s*[:：]?\s*[A-Za-z0-9_-]+)?|(?:候选|同簇|本簇)\s*[:：]?\s*[cs]\d(?:[A-Za-z0-9_-]*)|见\s+[cs]\d+-[A-Za-z0-9_-]+')


def placeholder(value):
    return isinstance(value, str) and bool(re.fullmatch(r'(?:<[^<>]+>|\$\{[A-Z][A-Z0-9_]*\})', value, re.I))


def private_address(value):
    try:
        address = ipaddress.ip_address(value)
        return any(address.version == network.version and address in network for network in NETWORKS)
    except ValueError:
        return False


class Redactor:
    def __init__(self, policy=None):
        policy = {} if policy is None else policy
        if not isinstance(policy, dict) or set(policy) - {'path_aliases', 'private_terms'}:
            raise ValueError('privacy policy supports path_aliases and private_terms only')
        self.path_aliases = []
        if not isinstance(policy.get('path_aliases', []), list):
            raise ValueError('path_aliases must be a list')
        for row in policy.get('path_aliases', []):
            if not isinstance(row, dict):
                raise ValueError('path aliases require prefix and replacement objects')
            prefix, replacement = row.get('prefix'), row.get('replacement')
            if (not isinstance(prefix, str) or len(prefix) < 3 or
                    not (prefix.startswith(('/', '~/')) or re.match(r'^[A-Za-z]:[\\/]', prefix)) or
                    not isinstance(replacement, str) or not re.fullmatch(r'\$\{[A-Z][A-Z0-9_]*\}', replacement)):
                raise ValueError('path aliases require a local absolute or home-relative prefix and a portable variable')
            self.path_aliases.append((prefix.rstrip('/\\'), replacement))
        self.path_aliases.sort(key=lambda row: len(row[0]), reverse=True)
        self.terms = policy.get('private_terms', [])
        if not isinstance(self.terms, list) or any(not isinstance(s, str) or len(s) < 4 for s in self.terms):
            raise ValueError('private_terms must be strings of at least four characters')
        self.counts = Counter()
        self.aliases = {}

    def mask(self, kind, value):
        if value is None or placeholder(value):
            return value
        self.counts[kind] += 1
        key = (kind, str(value))
        if key not in self.aliases:
            number = 1 + sum(k[0] == kind for k in self.aliases)
            self.aliases[key] = '${PRIVATE_' + kind.upper() + '_' + str(number) + '}'
        return self.aliases[key]

    def path(self, value):
        if re.match(r'^/(?:home|Users)/<[^<>]+>(?:/|$)', value):
            return value
        for prefix, replacement in self.path_aliases:
            if value == prefix or value.startswith((prefix + '/', prefix + '\\')):
                self.counts['path'] += 1
                return replacement + value[len(prefix):]
        return self.mask('path', value)

    def url(self, value):
        try:
            parsed = urlsplit(value)
            host = parsed.hostname or ''
            netloc = parsed.netloc
            if parsed.username is not None and not (parsed.username == 'git' and parsed.password is None):
                netloc = self.mask('credential', netloc.rsplit('@', 1)[0]) + '@' + netloc.rsplit('@', 1)[-1]
            if private_address(host.rstrip('.')) or PRIVATE_HOST.fullmatch(host.rstrip('.')) or (re.fullmatch(r'[A-Za-z0-9_-]+', host) and host != 'localhost' and not placeholder(host)):
                public_host = self.mask('host', host.rstrip('.')) + ('.' if host.endswith('.') else '')
                host_pattern = re.escape('[' + host + ']' if ':' in host else host)
                userinfo, separator, endpoint = netloc.rpartition('@')
                endpoint = re.sub(host_pattern, lambda match: public_host,
                                  endpoint if separator else netloc, count=1, flags=re.I)
                netloc = userinfo + separator + endpoint if separator else endpoint
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            if any(SECRET_KEY.fullmatch(key) or key.lower() == 'token' for key, _ in pairs):
                query = urlencode([(key, self.mask('credential', item) if SECRET_KEY.fullmatch(key) or key.lower() == 'token'
                                    else item) for key, item in pairs])
            else:
                query = parsed.query
            return urlunsplit((parsed.scheme, netloc, parsed.path, query, parsed.fragment))
        except ValueError:
            return self.mask('url', value)

    def text(self, value, key=''):
        # Decode structured strings before substitution, preserving JSON tool arguments.
        try:
            decoded = json.loads(value)
        except ValueError:
            decoded = None
        if isinstance(decoded, (dict, list)):
            return json.dumps(self.clean(decoded), ensure_ascii=False, sort_keys=True)
        for term in self.terms:
            if term in value:
                value = value.replace(term, self.mask('term', term))
        lines, password_prompt = [], False
        for line in value.splitlines(keepends=True):
            if 'expect' in line:
                password_prompt = bool(re.search(r'(?i)(password|assword|密码)', line))
            if password_prompt and re.search(r'\bsend\b', line):
                line = re.sub(r'(\bsend[ \t]+(?:--[ \t]+)?["\'])(.*?)(\\r["\'])',
                              lambda m: m[1] + self.mask('credential', m[2]) + m[3], line)
                password_prompt = False
            lines.append(line)
        value = ''.join(lines)
        # URL paths are public source locators, not local filesystem paths.
        parts, previous = [], 0
        for match in URL.finditer(value):
            parts.extend([self.plain(value[previous:match.start()], key), self.url(match[0])])
            previous = match.end()
        parts.append(self.plain(value[previous:], key))
        return ''.join(parts)

    def plain(self, value, key=''):
        value = re.sub(r'(?im)(\b(?:authorization|cookie|set-cookie)[ \t]*:[ \t]*)([^\r\n]+)',
                       lambda m: m[1] + self.mask('credential', m[2]), value)
        value = re.sub(r'(?<![\w-])((?:AK|SK)[ \t]*[:=][ \t]*)([A-Za-z0-9/+_=.-]{16,})(?!\w)',
                       lambda m: m[1] + self.mask('credential', m[2]), value)
        value = re.sub(r'''(?<![\w-])((?:AK|SK)[ \t]*[:=][ \t]*)(["'])([^\r\n]*?)\2''',
                       lambda m: m[1] + m[2] + self.mask('credential', m[3]) + m[2], value)
        def assignment(match):
            prefix, literal = match.groups()
            quote = literal[0] if literal[:1] in {'"', "'"} else ''
            content = literal[1:-1] if quote else literal
            if placeholder(content) or (re.search(r'(?i)\btoken["\']?\s*[:=：]', prefix) and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|0x[0-9a-fA-F]+', content)):
                return match[0]
            return prefix + quote + self.mask('credential', content) + quote
        value = ASSIGNMENT.sub(assignment, value)
        value = re.sub(r'(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]+',
                       lambda m: m[1] + self.mask('credential', m[0][len(m[1]):]), value)
        value = re.sub(r'((?:账号密码|密码)[ \t]*(?:[:=：][ \t]*)?)[A-Za-z0-9_!@#%^&*()+=./\\-]{4,}',
                       lambda m: m[1] + self.mask('credential', m[0][len(m[1]):]), value)
        for prefix, _ in self.path_aliases:
            value = re.sub(r'(?<![\w}>/])' + re.escape(prefix) + r'(?=$|[\\/\s\'"`;,])(?:[\\/][^\s\'"`<>;,)|}\]]*)?',
                           lambda m: self.path(m[0]), value)
        value = QUOTED_PATH.sub(lambda m: m[1] + self.path(m[2]) + m[1], value)
        value = PRIVATE_PATH.sub(lambda m: self.path(m[0]), value)
        def address(match):
            before = value[max(0, match.start()-24):match.start()]
            version = key.lower() in VERSION_KEYS or re.search(r'(?i)(?:version|release|build|CANN|CUDA|torch)\s*[:=]?\s*["\']?$', before)
            return self.mask('host', match[0]) if private_address(match[0]) and not version else match[0]
        value = IPV4.sub(address, value)
        value = re.sub(r'(?<![\w:])(?:[A-Fa-f0-9]{0,4}:){2,}[A-Fa-f0-9:]{0,39}(?![\w:])',
                       lambda m: self.mask('host', m[0]) if private_address(m[0]) else m[0], value)
        value = EMAIL.sub(lambda m: m[0] if m[0].startswith('git@') and value[m.end():m.end()+1] == ':'
                          and not PRIVATE_HOST.search(m[0]) else self.mask('email', m[0]), value)
        value = PRIVATE_HOST.sub(lambda m: m[0] if value[m.end():m.end()+1] == '('
                                 else self.mask('host', m[0]), value)
        def ssh_target(match):
            user, host = match.groups()
            before = value[max(0, value.rfind('\n', 0, match.start())+1):match.start()]
            if user == 'git' and '.' in host and not PRIVATE_HOST.fullmatch(host):
                return match[0]
            if re.search(r'\b(?:ssh|scp|sftp|rsync)\b', before) or value[match.end():match.end()+1] == ':':
                return self.mask('identity', user) + '@' + self.mask('host', host)
            return match[0]
        value = re.sub(r'(?<![\w])([A-Za-z0-9._-]+)@([A-Za-z0-9_.-]+)(?=[:\s]|$)', ssh_target, value)
        return value

    def clean(self, value, key='', ancestry=()):
        if isinstance(value, dict):
            result = {}
            token_data = bool({'logprob', 'logprobs', 'logits', 'token_id', 'token_ids',
                               'input_ids', 'output_ids', 'token_count'} & value.keys())
            for name, item in value.items():
                lower = name.lower()
                if SECRET_KEY.fullmatch(name) and item is not None and not (lower in {'ak', 'sk'} and not isinstance(item, str)):
                    result[name] = self.mask('credential', item)
                elif lower == 'token' and isinstance(item, str) and not token_data:
                    result[name] = self.mask('credential', item)
                elif lower in {'username', 'user_name', 'email', 'email_address', 'account_id', 'user_id'} and item is not None:
                    result[name] = self.mask('identity', item)
                elif lower in {'name', 'id'} and ancestry and ancestry[-1] in {'user', 'author', 'account', 'owner'}:
                    result[name] = self.mask('identity', item)
                elif lower in PATH_KEYS and isinstance(item, str) and (re.match('^' + ROOT, item) or
                        any(item == prefix or item.startswith((prefix+'/', prefix+'\\')) for prefix, _ in self.path_aliases)):
                    result[name] = self.path(item)
                elif lower in {'host', 'hostname', 'address', 'ip'} and isinstance(item, str) and not placeholder(item) and (
                        private_address(item) or PRIVATE_HOST.fullmatch(item) or
                        (re.fullmatch(r'[A-Za-z0-9_-]+', item) and item != 'localhost')):
                    result[name] = self.mask('host', item)
                else:
                    result[name] = self.clean(item, lower, (*ancestry, lower))
            return result
        if isinstance(value, list):
            return [self.clean(item, key, ancestry) for item in value]
        return self.text(value, key) if isinstance(value, str) else value


def publication_findings(text, policy=None):
    """Return only category/line coordinates; findings never echo sensitive values."""
    redactor, result = Redactor(policy), []
    for number, line in enumerate(text.splitlines(), 1):
        before = redactor.counts.copy()
        redactor.text(line)
        for category in sorted((redactor.counts - before)):
            result.append({'line': number, 'category': 'privacy_' + category})
        if INTERNAL_REFERENCE.search(line):
            result.append({'line': number, 'category': 'unresolved_internal_reference'})
    return result


def require_publication_clean(text, policy=None):
    findings = publication_findings(text, policy)
    if findings:
        summary = ', '.join(f"{row['category']} at line {row['line']}" for row in findings[:12])
        raise ValueError('publication audit failed: ' + summary)
