"""Shared machine contract for cannbot-knowledge paths and frontmatter."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


ID_RE = re.compile(r"^[a-z0-9_]+$")
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
ACTOR_RE = re.compile(r"^(?:human:[^\s/:]+|process:[^\s/:]+|[^\s/:]+/[^\s/]+)$")
INLINE_LINK_RE = re.compile(r"(!?)\[[^\]\n]*\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"(!?)\[([^\]\n]*)\]\[([^\]\n]*)\]")
REFERENCE_DEFINITION_RE = re.compile(
    r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))"
)
GIT_VIEW_HOSTS = {
    "bitbucket.org",
    "codeberg.org",
    "gitcode.com",
    "github.com",
    "gitee.com",
    "gitlab.com",
}
RAW_GIT_HOSTS = {"raw.gitcode.com", "raw.githubusercontent.com"}
OKF_VERSION = "0.2"
FREELY_NESTED_PROFILES = {"apis", "concepts", "examples", "guides", "optimizations"}


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None,
                None,
                f"expected a mapping node, but found {node.id}",
                node.start_mark,
            )
        self.flatten_mapping(node)
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable key",
                    key_node.start_mark,
                ) from exc
            if duplicate:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key: {key}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def _yaml_load(text: str) -> Any:
    return yaml.load(text, Loader=UniqueKeySafeLoader)


@dataclass(frozen=True)
class Issue:
    code: str
    message: str


@dataclass(frozen=True)
class PathInfo:
    domain: str
    route: str | None
    card_type: str
    doc_id: str


def _mapping(path: Path) -> dict[str, Any]:
    data = _yaml_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("unterminated frontmatter") from exc
    metadata = _yaml_load("\n".join(lines[1:end])) or {}
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata, "\n".join(lines[end + 1 :]).strip()


class Contract:
    def __init__(self, root: Path):
        self.root = root.resolve()
        schema_path = self.root / "governance/schemas/frontmatter.schema.json"
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(self.schema)
        self.schema_validator = Draft202012Validator(self.schema, format_checker=FormatChecker())

        profile_data = _mapping(self.root / "governance/schemas/profiles.yaml")
        self.common_fields = set(profile_data.get("common_required", []))
        self.profiles = profile_data.get("profiles")
        if not isinstance(self.profiles, dict) or not self.profiles:
            raise ValueError("profiles.yaml must define a non-empty profiles mapping")
        self.types = set(self.profiles)

        self.registries = _mapping(self.root / "governance/schemas/registries.yaml")
        self.domains = self._section("domains")
        self.technologies = self._section("technologies")
        self.scopes = self._section("scopes")
        self.platforms = self._section("platforms")
        self.tags = self._section("tags")
        self.local_sources = self._section("local_sources")
        self.path_values = self._section("paths")
        self.routes = set(self.technologies) | set(self.scopes)
        self.operator_families = self._string_set("operator_families")
        self.operator_categories = self._string_set("operator_categories")
        self.runbook_areas = self._string_set("runbook_areas")
        self._validate_registry_contract()

    def _section(self, name: str) -> dict[str, Any]:
        value = self.registries.get(name)
        if not isinstance(value, dict):
            raise ValueError(f"registries.yaml must define a {name} mapping")
        return value

    def _string_set(self, name: str) -> set[str]:
        value = self.path_values.get(name)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
            raise ValueError(f"registries paths.{name} must be a non-empty string list")
        if len(value) != len(set(value)):
            raise ValueError(f"registries paths.{name} contains duplicates")
        return set(value)

    def _validate_registry_contract(self) -> None:
        if set(self.technologies) & set(self.scopes):
            overlap = ", ".join(sorted(set(self.technologies) & set(self.scopes)))
            raise ValueError(f"technology and scope IDs overlap: {overlap}")
        for section_name, section in (
            ("domains", self.domains),
            ("technologies", self.technologies),
            ("scopes", self.scopes),
            ("platforms", self.platforms),
        ):
            for item_id, item in section.items():
                if not isinstance(item_id, str) or not ID_RE.fullmatch(item_id):
                    raise ValueError(f"invalid {section_name} ID: {item_id}")
                if not isinstance(item, dict) or not str(item.get("description", "")).strip():
                    raise ValueError(f"{section_name}.{item_id} requires a description")
        for domain_id, domain in self.domains.items():
            direct_types = domain.get("direct_types")
            if not isinstance(direct_types, list) or set(direct_types) - self.types:
                raise ValueError(f"domains.{domain_id}.direct_types contains unknown types")
            if not isinstance(domain.get("precreate_routes", False), bool):
                raise ValueError(f"domains.{domain_id}.precreate_routes must be a boolean")
        for profile_id, profile in self.profiles.items():
            if not isinstance(profile, dict) or not str(profile.get("okf_type", "")).strip():
                raise ValueError(f"profiles.{profile_id} requires a non-empty okf_type")
        for route_id, route in {**self.technologies, **self.scopes}.items():
            domains = route.get("domains")
            if not isinstance(domains, list) or not domains or set(domains) - set(self.domains):
                raise ValueError(f"route {route_id} must declare registered domains")
        for tag_id, tag in self.tags.items():
            if not isinstance(tag, dict):
                raise ValueError(f"tags.{tag_id} must be a mapping")
            dimension = tag.get("dimension")
            if dimension not in {"task", "topic", "paradigm"} or not tag_id.startswith(f"{dimension}."):
                raise ValueError(f"tags.{tag_id} has inconsistent dimension: {dimension}")
            if not str(tag.get("description", "")).strip():
                raise ValueError(f"tags.{tag_id} requires a description")
        for category in self.operator_categories:
            if not ID_RE.fullmatch(category) or not category.endswith("s"):
                raise ValueError(f"operator category must use a plural snake_case ID: {category}")
        for source_id, source in self.local_sources.items():
            if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id):
                raise ValueError(f"invalid local_sources ID: {source_id}")
            if not isinstance(source, dict) or not str(source.get("description", "")).strip():
                raise ValueError(f"local_sources.{source_id} requires a description")
            root = source.get("root")
            if (
                not isinstance(root, str)
                or Path(root).parts != (root,)
                or root in {"", ".", ".."}
                or "\\" in root
            ):
                raise ValueError(f"local_sources.{source_id}.root must be a top-level relative path")
            fetch_script = source.get("fetch_script")
            if (
                not isinstance(fetch_script, str)
                or not self._safe_repository_path(fetch_script).is_absolute()
            ):
                raise ValueError(
                    f"local_sources.{source_id}.fetch_script must be a safe repository path"
                )
            archive_sha256 = source.get("archive_sha256")
            if not isinstance(archive_sha256, str) or not re.fullmatch(
                r"[0-9a-f]{64}", archive_sha256
            ):
                raise ValueError(
                    f"local_sources.{source_id}.archive_sha256 must be lowercase SHA-256"
                )

    def _safe_repository_path(self, value: str) -> Path:
        if value != value.strip() or "\\" in value:
            return Path()
        relative = Path(value)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            return Path()
        try:
            resolved = (self.root / relative).resolve()
            resolved.relative_to(self.root)
        except ValueError:
            return Path()
        return resolved

    def route_domains(self, route: str) -> set[str]:
        value = self.technologies.get(route) or self.scopes.get(route)
        if not isinstance(value, dict):
            return set()
        return set(value.get("domains", []))

    def okf_type(self, card_type: str) -> str:
        profile = self.profiles.get(card_type)
        if not isinstance(profile, dict) or not isinstance(profile.get("okf_type"), str):
            raise ValueError(f"invalid profile: {card_type}")
        return profile["okf_type"]

    def derive_card_path(self, relative: Path) -> PathInfo:
        if relative.is_absolute() or relative.suffix != ".md" or relative.name == "index.md":
            raise ValueError("card path must be a non-index Markdown path under knowledge/")
        parts = relative.parts
        if not parts or parts[0] != "knowledge" or ".." in parts:
            raise ValueError("card path must stay under knowledge/")
        if not ID_RE.fullmatch(relative.stem):
            raise ValueError("card filename must use lowercase snake_case")
        if len(parts) < 4:
            raise ValueError("card path is missing a knowledge type")
        domain = parts[1]
        if domain not in self.domains:
            raise ValueError(f"unregistered knowledge domain: {domain}")

        type_indexes = [index for index, part in enumerate(parts[:-1]) if part in self.types]
        if len(type_indexes) != 1:
            raise ValueError("card path must contain exactly one registered knowledge type")
        type_index = type_indexes[0]
        card_type = parts[type_index]
        route: str | None
        if type_index == 2:
            route = None
            if card_type not in set(self.domains[domain].get("direct_types", [])):
                raise ValueError(f"domain {domain} does not allow direct type: {card_type}")
        elif type_index == 3:
            route = parts[2]
            if route not in self.routes:
                raise ValueError(f"unregistered technology or scope: {route}")
            if domain not in self.route_domains(route):
                raise ValueError(f"route {route} is not allowed under domain {domain}")
        else:
            raise ValueError("path must be domain/type or domain/technology-or-scope/type")

        suffix = parts[type_index + 1 : -1]
        if card_type == "operators":
            if len(suffix) != 2 or suffix[0] not in self.operator_families:
                allowed = "|".join(sorted(self.operator_families))
                raise ValueError(f"operator path must be operators/<{allowed}>/<category>/<operator>.md")
            if suffix[1] not in self.operator_categories:
                raise ValueError(f"unregistered operator category: {suffix[1]}")
        elif card_type == "runbooks":
            if len(suffix) != 1 or suffix[0] not in self.runbook_areas:
                allowed = "|".join(sorted(self.runbook_areas))
                raise ValueError(f"runbook path must be runbooks/<{allowed}>/<runbook>.md")
        elif card_type in FREELY_NESTED_PROFILES:
            if any(not ID_RE.fullmatch(part) for part in suffix):
                raise ValueError(f"{card_type} subdirectories must use lowercase snake_case")
        elif suffix:
            raise ValueError(f"{card_type} cards cannot add unregistered subdirectories")
        if card_type == "interoperability" and route != "shared":
            raise ValueError("interoperability cards must be placed under a shared scope")
        bundle_relative = Path(*relative.parts[1:])
        return PathInfo(domain, route, card_type, bundle_relative.with_suffix("").as_posix())

    def validate_index_frontmatter(
        self,
        relative: Path,
        metadata: dict[str, Any] | None,
    ) -> list[Issue]:
        if relative == Path("knowledge/index.md"):
            if metadata != {"okf_version": OKF_VERSION}:
                return [
                    Issue(
                        "index.frontmatter",
                        f"bundle root index.md requires only okf_version: {OKF_VERSION}",
                    )
                ]
            return []
        if metadata is not None:
            return [Issue("index.frontmatter", "only the bundle root index.md may have frontmatter")]
        return []

    def validate_index_path(self, relative: Path) -> list[Issue]:
        if relative.name != "index.md" or not relative.parts or relative.parts[0] != "knowledge":
            return [Issue("index.path", "index.md must stay under knowledge/")]
        parts = relative.parts[:-1]
        if parts == ("knowledge",):
            return []
        domain = parts[1] if len(parts) > 1 else ""
        if domain not in self.domains:
            return [Issue("index.domain", f"unregistered knowledge domain: {domain}")]
        if len(parts) == 2:
            return []

        route: str | None = None
        card_type: str | None = None
        tail: tuple[str, ...] = ()
        if parts[2] in self.types:
            card_type = parts[2]
            if card_type not in set(self.domains[domain].get("direct_types", [])):
                return [Issue("index.type", f"domain {domain} does not allow direct type: {card_type}")]
            tail = parts[3:]
        else:
            route = parts[2]
            if route not in self.routes:
                return [Issue("index.route", f"unregistered technology or scope: {route}")]
            if domain not in self.route_domains(route):
                return [Issue("index.route", f"route {route} is not allowed under domain {domain}")]
            if len(parts) == 3:
                return []
            card_type = parts[3]
            if card_type not in self.types:
                return [Issue("index.type", f"unregistered knowledge type: {card_type}")]
            tail = parts[4:]

        if card_type == "operators":
            if len(tail) > 2:
                return [Issue("index.operator", "operator index is deeper than family/category")]
            if tail and tail[0] not in self.operator_families:
                return [Issue("index.operator", f"unregistered operator family: {tail[0]}")]
            if len(tail) == 2 and tail[1] not in self.operator_categories:
                return [Issue("index.operator", f"unregistered operator category: {tail[1]}")]
        elif card_type == "runbooks":
            if len(tail) > 1 or (tail and tail[0] not in self.runbook_areas):
                return [Issue("index.runbook", "runbook index must stop at a registered area")]
        elif card_type in FREELY_NESTED_PROFILES:
            if any(not ID_RE.fullmatch(part) for part in tail):
                return [Issue("index.depth", f"{card_type} subdirectories must use lowercase snake_case")]
        elif tail:
            return [Issue("index.depth", f"{card_type} index has an unregistered subdirectory")]
        if card_type == "interoperability" and route != "shared":
            return [Issue("index.route", "interoperability must be placed under a shared scope")]
        return []

    def validate_card(
        self,
        relative: Path,
        metadata: dict[str, Any],
        body: str,
        *,
        check_replacement: bool = True,
    ) -> list[Issue]:
        issues: list[Issue] = []
        try:
            path_info = self.derive_card_path(relative)
        except ValueError as exc:
            return [Issue("path.invalid", str(exc))]

        for error in sorted(self.schema_validator.iter_errors(metadata), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "frontmatter"
            issues.append(Issue("frontmatter.schema", f"{location}: {error.message}"))

        profile = self.profiles[path_info.card_type]
        if not isinstance(profile, dict):
            return issues + [Issue("frontmatter.profile", f"invalid profile: {path_info.card_type}")]
        required = self.common_fields | set(profile.get("required", []))
        allowed = required | set(profile.get("optional", []))
        for field in sorted(required - set(metadata)):
            issues.append(Issue("frontmatter.required", f"missing required field: {field}"))
        for field in sorted(set(metadata) - allowed):
            issues.append(Issue("frontmatter.extra", f"field is not allowed by {path_info.card_type} profile: {field}"))

        if not body.strip():
            issues.append(Issue("body.empty", "knowledge card body is empty"))
        for field in ("title", "description"):
            value = metadata.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(Issue("frontmatter.text", f"{field} must be a non-empty string"))

        if metadata.get("type") != self.okf_type(path_info.card_type):
            issues.append(
                Issue(
                    "frontmatter.type",
                    f"type must be {self.okf_type(path_info.card_type)} for {path_info.card_type}",
                )
            )

        self._validate_tags(metadata, issues)
        self._validate_sources(metadata, issues)
        self._validate_times(metadata, issues)
        self._validate_verified(metadata, issues)
        self._validate_platforms(path_info.card_type, metadata, issues)
        self._validate_lifecycle(path_info.doc_id, metadata, check_replacement, issues)
        self._validate_interoperability(path_info.card_type, metadata, issues)
        return _deduplicate(issues)

    def _validate_tags(self, metadata: dict[str, Any], issues: list[Issue]) -> None:
        tags = metadata.get("tags")
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            return
        dimensions: set[str] = set()
        for tag in tags:
            definition = self.tags.get(tag)
            if not isinstance(definition, dict):
                issues.append(Issue("tag.unknown", f"unregistered tag: {tag}"))
            else:
                dimensions.add(str(definition.get("dimension")))
        for required in ("task", "topic"):
            if required not in dimensions:
                issues.append(Issue(f"tag.{required}", f"at least one {required} tag is required"))

    def _validate_sources(self, metadata: dict[str, Any], issues: list[Issue]) -> None:
        sources = metadata.get("sources")
        if not isinstance(sources, list):
            return
        if metadata.get("status") != "draft" and not sources:
            issues.append(Issue("source.required", "non-draft card requires at least one source"))
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            resource = source.get("resource")
            if not isinstance(resource, str) or not resource.strip():
                issues.append(
                    Issue("source.resource", f"sources[{index}].resource must be non-empty")
                )
            elif re.match(r"^https?://", resource):
                parsed = urlparse(resource)
                if not parsed.netloc or parsed.username is not None or parsed.password is not None:
                    issues.append(
                        Issue(
                            "source.resource",
                            f"sources[{index}].resource is not a canonical HTTP(S) URL",
                        )
                    )
                elif not _git_url_is_pinned(resource):
                    issues.append(
                        Issue(
                            "source.pin",
                            f"sources[{index}] Git resource is not pinned to a 40-hex commit",
                        )
                    )
            elif not self._is_safe_local_resource(resource):
                issues.append(
                    Issue(
                        "source.resource",
                        f"sources[{index}].resource must be an HTTP(S) URL or registered local source",
                    )
                )

    def _is_safe_local_resource(self, resource: str) -> bool:
        if resource != resource.strip() or "\\" in resource:
            return False
        parsed = urlparse(resource)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            return False
        relative = Path(resource)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            return False
        if relative.as_posix() != resource or len(relative.parts) < 2:
            return False
        try:
            (self.root / relative).resolve().relative_to(self.root.resolve())
        except ValueError:
            return False
        registered_roots = {str(source["root"]) for source in self.local_sources.values()}
        return relative.parts[0] in registered_roots

    def _validate_times(self, metadata: dict[str, Any], issues: list[Issue]) -> None:
        parsed: dict[str, datetime] = {}
        for field in ("created_at", "updated_at"):
            value = metadata.get(field)
            if not isinstance(value, str) or not RFC3339_UTC_RE.fullmatch(value):
                issues.append(Issue("frontmatter.time", f"{field} must use UTC RFC3339 seconds ending in Z"))
                continue
            try:
                parsed[field] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                issues.append(Issue("frontmatter.time", f"{field} is not a valid UTC calendar time"))
        if len(parsed) == 2 and parsed["updated_at"] < parsed["created_at"]:
            issues.append(Issue("frontmatter.time_order", "updated_at is earlier than created_at"))

    def _validate_verified(self, metadata: dict[str, Any], issues: list[Issue]) -> None:
        value = metadata.get("verified")
        if value is None:
            return
        events = value if isinstance(value, list) else [value]
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                continue
            actor = event.get("by")
            if not isinstance(actor, str) or not ACTOR_RE.fullmatch(actor):
                issues.append(
                    Issue(
                        "verified.actor",
                        f"verified[{index}].by must use human:<id>, process:<id>, or <producer>/<version>",
                    )
                )

    def _validate_platforms(self, card_type: str, metadata: dict[str, Any], issues: list[Issue]) -> None:
        if card_type == "glossaries":
            return
        platforms = metadata.get("platforms")
        if not isinstance(platforms, list) or not all(isinstance(item, str) for item in platforms):
            return
        if not platforms and metadata.get("status") != "draft":
            issues.append(Issue("platform.unknown", "empty platforms requires status draft"))
        if "agnostic" in platforms and len(platforms) != 1:
            issues.append(Issue("platform.agnostic", "agnostic cannot be combined with concrete platforms"))
        for platform in platforms:
            if platform not in self.platforms:
                issues.append(Issue("platform.unknown", f"unregistered platform: {platform}"))

    def _validate_lifecycle(
        self,
        doc_id: str,
        metadata: dict[str, Any],
        check_replacement: bool,
        issues: list[Issue],
    ) -> None:
        status = metadata.get("status")
        replaced_by = metadata.get("replaced_by")
        if replaced_by is None:
            return
        if status != "deprecated":
            issues.append(Issue("status.replaced_by", "replaced_by requires deprecated status"))
            return
        if (
            not isinstance(replaced_by, str)
            or replaced_by.startswith(("/", "knowledge/"))
            or replaced_by.endswith(".md")
            or ".." in Path(replaced_by).parts
        ):
            issues.append(
                Issue(
                    "status.replaced_by",
                    "replaced_by must be a bundle-relative Concept ID without .md",
                )
            )
            return
        if replaced_by == doc_id:
            issues.append(Issue("status.replaced_by", "replaced_by cannot reference the current card"))
        if check_replacement and not (self.root / "knowledge" / f"{replaced_by}.md").is_file():
            issues.append(Issue("status.replaced_by", f"replacement card does not exist: {replaced_by}"))

    def _validate_interoperability(
        self,
        card_type: str,
        metadata: dict[str, Any],
        issues: list[Issue],
    ) -> None:
        if card_type != "interoperability":
            return
        source = metadata.get("source_technology")
        target = metadata.get("target_technology")
        if source not in self.technologies or target not in self.technologies:
            issues.append(Issue("technology.value", "source and target technology must be registered"))
        if source == target:
            issues.append(Issue("technology.same", "source and target technology must differ"))

    def validate_index_tree(self) -> list[tuple[Path, Issue]]:
        knowledge_root = self.root / "knowledge"
        results: list[tuple[Path, Issue]] = []
        structural = self.structural_directories()
        for relative in sorted(structural):
            directory = self.root / relative
            if not directory.is_dir():
                results.append(
                    (
                        directory,
                        Issue(
                            "structure.missing",
                            "required domain or predeclared route directory is missing",
                        ),
                    )
                )
        for directory in sorted(path for path in knowledge_root.rglob("*") if path.is_dir()):
            index = directory / "index.md"
            if not index.is_file():
                results.append((directory, Issue("index.missing", "knowledge directory requires index.md")))
                continue
            children = [item for item in directory.iterdir() if item.name != "index.md"]
            if not children and directory.relative_to(self.root) not in structural:
                results.append((directory, Issue("index.empty", "directory has no real knowledge content")))
            results.extend((index, issue) for issue in self.validate_index_path(index.relative_to(self.root)))
            results.extend((index, issue) for issue in self._validate_index_links(index))
        root_index = knowledge_root / "index.md"
        if not root_index.is_file():
            results.append((knowledge_root, Issue("index.missing", "knowledge root requires index.md")))
        else:
            results.extend((root_index, issue) for issue in self.validate_index_path(root_index.relative_to(self.root)))
            results.extend((root_index, issue) for issue in self._validate_index_links(root_index))
        return results

    def validate_repository_infrastructure(self) -> list[tuple[Path, Issue]]:
        """Validate repository files required by registered local-source workflows."""
        results: list[tuple[Path, Issue]] = []
        for source_id, definition in self.local_sources.items():
            fetch_script = self._safe_repository_path(str(definition["fetch_script"]))
            if not fetch_script.is_file():
                results.append(
                    (
                        self.root / "governance/schemas/registries.yaml",
                        Issue(
                            "source.fetch_script_missing",
                            f"local source {source_id} fetch script does not exist: "
                            f"{fetch_script.relative_to(self.root)}",
                        ),
                    )
                )
            elif not os.access(fetch_script, os.X_OK):
                results.append(
                    (
                        fetch_script,
                        Issue(
                            "source.fetch_script_mode",
                            f"local source {source_id} fetch script must be executable",
                        ),
                    )
                )
        return results

    def structural_directories(self) -> set[Path]:
        """Return domain roots and routes predeclared by their domain Registry policy."""
        result = {Path("knowledge") / domain for domain in self.domains}
        precreated_domains = {
            domain
            for domain, definition in self.domains.items()
            if definition.get("precreate_routes", False)
        }
        for route in sorted(self.routes):
            for domain in self.route_domains(route) & precreated_domains:
                result.add(Path("knowledge") / domain / route)
        return result

    def _validate_index_links(self, index: Path) -> list[Issue]:
        text = index.read_text(encoding="utf-8")
        expected: set[Path] = set()
        for child in index.parent.iterdir():
            if child.name == "index.md":
                continue
            if child.is_dir() and (child / "index.md").is_file():
                expected.add((child / "index.md").resolve())
            elif child.is_file() and child.suffix == ".md":
                expected.add(child.resolve())

        actual: list[Path] = []
        issues: list[Issue] = []
        for target_text, _ in markdown_targets(text):
            if not target_text or target_text.startswith(("http://", "https://", "#", "mailto:")):
                continue
            clean = unquote(target_text.split("#", 1)[0])
            if not clean:
                continue
            if clean.startswith("/"):
                target = (self.root / "knowledge" / clean.lstrip("/")).resolve()
            else:
                target = (index.parent / clean).resolve()
            actual.append(target)
            if target not in expected:
                issues.append(Issue("index.non_direct", f"index links a non-direct child: {target_text}"))
        for target in sorted(expected - set(actual)):
            issues.append(Issue("index.unlisted", f"direct child is not listed: {target.relative_to(index.parent)}"))
        if len(actual) != len(set(actual)):
            issues.append(Issue("index.duplicate", "index contains duplicate local targets"))
        return issues


def _git_url_is_pinned(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host in GIT_VIEW_HOSTS:
        for marker in ("blob", "tree", "raw"):
            if marker in parts:
                index = parts.index(marker)
                return index + 1 < len(parts) and bool(COMMIT_RE.fullmatch(parts[index + 1]))
        if host == "bitbucket.org" and "src" in parts:
            index = parts.index("src")
            return index + 1 < len(parts) and bool(COMMIT_RE.fullmatch(parts[index + 1]))
        if host == "codeberg.org" and "src" in parts:
            index = parts.index("src")
            return (
                index + 2 < len(parts)
                and parts[index + 1] == "commit"
                and bool(COMMIT_RE.fullmatch(parts[index + 2]))
            )
        return False
    if host == "raw.gitcode.com" and "raw" in parts:
        index = parts.index("raw")
        return index + 1 < len(parts) and bool(COMMIT_RE.fullmatch(parts[index + 1]))
    if host == "raw.githubusercontent.com" and len(parts) >= 3:
        return bool(COMMIT_RE.fullmatch(parts[2]))
    return host not in RAW_GIT_HOSTS


def _reference_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _markdown_destination(value: str) -> str:
    return value.split()[0].strip("<>")


def markdown_targets(text: str) -> list[tuple[str, bool]]:
    """Return Markdown destinations as ``(target, is_image)`` pairs."""
    results = [
        (_markdown_destination(match.group(2)), bool(match.group(1)))
        for match in INLINE_LINK_RE.finditer(text)
    ]
    definitions = {
        _reference_label(match.group(1)): (match.group(2) or match.group(3))
        for match in REFERENCE_DEFINITION_RE.finditer(text)
    }
    for match in REFERENCE_LINK_RE.finditer(text):
        label = _reference_label(match.group(3) or match.group(2))
        target = definitions.get(label)
        if target:
            results.append((_markdown_destination(target), bool(match.group(1))))
    return [(target, is_image) for target, is_image in results if target]


def relative_markdown_links(path: Path, bundle_root: Path | None = None) -> list[tuple[str, Path]]:
    results: list[tuple[str, Path]] = []
    for target_text, _ in markdown_targets(path.read_text(encoding="utf-8")):
        if not target_text or target_text.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = unquote(target_text.split("#", 1)[0])
        if clean:
            if clean.startswith("/") and bundle_root is not None:
                target = (bundle_root / clean.lstrip("/")).resolve()
            else:
                target = (path.parent / clean).resolve()
            results.append((target_text, target))
    return results


def _deduplicate(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, str]] = set()
    result: list[Issue] = []
    for issue in issues:
        key = (issue.code, issue.message)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result
