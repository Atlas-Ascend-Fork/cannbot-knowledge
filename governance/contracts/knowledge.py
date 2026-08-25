"""Shared machine contract for cannbot-knowledge paths and frontmatter."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from .schema import SchemaValidator


ID_RE = re.compile(r"^[a-z0-9_]+$")


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""

    def construct_mapping(
        self, node: MappingNode, deep: bool = False
    ) -> dict[Any, Any]:
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
    path: Path | None = None
    line: int | None = None
    details: str | None = None


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
        end = next(
            index for index in range(1, len(lines)) if lines[index].strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError("unterminated frontmatter") from exc
    metadata = _yaml_load("\n".join(lines[1:end])) or {}
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata, "\n".join(lines[end + 1 :]).strip()


class Contract:
    """Load governing data and expose compatibility entry points for consumers."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        schema_path = self.root / "governance/schemas/frontmatter.schema.json"
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.schema_validator = SchemaValidator(self.schema)

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
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) for item in value)
        ):
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
                if (
                    not isinstance(item, dict)
                    or not str(item.get("description", "")).strip()
                ):
                    raise ValueError(f"{section_name}.{item_id} requires a description")
        for domain_id, domain in self.domains.items():
            direct_types = domain.get("direct_types")
            if not isinstance(direct_types, list) or set(direct_types) - self.types:
                raise ValueError(
                    f"domains.{domain_id}.direct_types contains unknown types"
                )
            if not isinstance(domain.get("precreate_routes", False), bool):
                raise ValueError(
                    f"domains.{domain_id}.precreate_routes must be a boolean"
                )
        for profile_id, profile in self.profiles.items():
            if (
                not isinstance(profile, dict)
                or not str(profile.get("okf_type", "")).strip()
            ):
                raise ValueError(f"profiles.{profile_id} requires a non-empty okf_type")
        for route_id, route in {**self.technologies, **self.scopes}.items():
            domains = route.get("domains")
            if (
                not isinstance(domains, list)
                or not domains
                or set(domains) - set(self.domains)
            ):
                raise ValueError(f"route {route_id} must declare registered domains")
        for tag_id, tag in self.tags.items():
            if not isinstance(tag, dict):
                raise ValueError(f"tags.{tag_id} must be a mapping")
            dimension = tag.get("dimension")
            if dimension not in {"task", "topic", "paradigm"} or not tag_id.startswith(
                f"{dimension}."
            ):
                raise ValueError(
                    f"tags.{tag_id} has inconsistent dimension: {dimension}"
                )
            if not str(tag.get("description", "")).strip():
                raise ValueError(f"tags.{tag_id} requires a description")
        for category in self.operator_categories:
            if not ID_RE.fullmatch(category) or not category.endswith("s"):
                raise ValueError(
                    f"operator category must use a plural snake_case ID: {category}"
                )
        for source_id, source in self.local_sources.items():
            if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id):
                raise ValueError(f"invalid local_sources ID: {source_id}")
            if (
                not isinstance(source, dict)
                or not str(source.get("description", "")).strip()
            ):
                raise ValueError(f"local_sources.{source_id} requires a description")
            source_root = source.get("root")
            if (
                not isinstance(source_root, str)
                or Path(source_root).parts != (source_root,)
                or source_root in {"", ".", ".."}
                or "\\" in source_root
            ):
                raise ValueError(
                    f"local_sources.{source_id}.root must be a top-level relative path"
                )
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
        if not isinstance(profile, dict) or not isinstance(
            profile.get("okf_type"), str
        ):
            raise ValueError(f"invalid profile: {card_type}")
        return profile["okf_type"]

    def derive_card_path(self, relative: Path) -> PathInfo:
        from .checks.path import derive_card_path

        return derive_card_path(self, relative)

    def validate_index_frontmatter(
        self,
        relative: Path,
        metadata: dict[str, Any] | None,
    ) -> list[Issue]:
        from .checks.navigation import validate_index_frontmatter

        return validate_index_frontmatter(relative, metadata)

    def validate_index_path(self, relative: Path) -> list[Issue]:
        from .checks.navigation import validate_index_path

        return validate_index_path(self, relative)

    def validate_card(
        self,
        relative: Path,
        metadata: dict[str, Any],
        body: str,
    ) -> list[Issue]:
        from .checks import validate_card

        return validate_card(self, relative, metadata, body)

    def validate_index_tree(self) -> list[tuple[Path, Issue]]:
        from .checks.navigation import validate_index_tree

        return validate_index_tree(self)

    def validate_repository_infrastructure(self) -> list[tuple[Path, Issue]]:
        from .checks.local_sources import check_repository

        return check_repository(self)

    def structural_directories(self) -> set[Path]:
        from .checks.navigation import structural_directories

        return structural_directories(self)

def markdown_targets(text: str) -> list[tuple[str, bool]]:
    from .checks.links import markdown_targets as find_targets

    return find_targets(text)


def relative_markdown_links(
    path: Path,
    bundle_root: Path | None = None,
) -> list[tuple[str, Path]]:
    from .checks.links import relative_markdown_links as find_links

    return find_links(path, bundle_root)
