"""
Tests for the flux-skills SKILLS-REGISTRY, SKILL-SPEC, and CONFIG.yaml compliance.

Tests cover:
1. Skill spec compliance (required fields, sections)
2. CONFIG.yaml structure validation
3. Skills registry data
4. Fluxasm file structure validation
5. AGENT.md documentation compliance
"""

import os
import sys
import pytest
import yaml

# Base path for the repo
BASE = os.path.join(os.path.dirname(__file__), "..")

# Known skills in the repo
KNOWN_SKILLS = ["dreamer", "streamer", "mud-navigator", "spreader"]


# ===========================================================================
# Skill Spec Compliance Tests
# ===========================================================================

class TestSkillSpecCompliance:
    """Test that skills comply with SKILL-SPEC.md requirements."""

    def test_skill_spec_file_exists(self):
        path = os.path.join(BASE, "SKILL-SPEC.md")
        assert os.path.exists(path)

    def test_all_skills_have_agent_md(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            assert os.path.exists(path), f"Missing AGENT.md for {skill}"

    def test_all_skills_have_config_yaml(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "CONFIG.yaml")
            assert os.path.exists(path), f"Missing CONFIG.yaml for {skill}"

    def test_agent_md_has_what_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## WHAT" in content, f"Missing WHAT section in {skill}/AGENT.md"

    def test_agent_md_has_why_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## WHY" in content, f"Missing WHY section in {skill}/AGENT.md"

    def test_agent_md_has_how_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## HOW" in content, f"Missing HOW section in {skill}/AGENT.md"

    def test_agent_md_has_input_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## INPUT" in content, f"Missing INPUT section in {skill}/AGENT.md"

    def test_agent_md_has_output_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## OUTPUT" in content, f"Missing OUTPUT section in {skill}/AGENT.md"

    def test_agent_md_has_config_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## CONFIG" in content, f"Missing CONFIG section in {skill}/AGENT.md"

    def test_agent_md_has_modify_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## MODIFY" in content, f"Missing MODIFY section in {skill}/AGENT.md"

    def test_agent_md_has_compose_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## COMPOSE" in content, f"Missing COMPOSE section in {skill}/AGENT.md"

    def test_agent_md_has_feedback_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## FEEDBACK" in content, f"Missing FEEDBACK section in {skill}/AGENT.md"

    def test_agent_md_has_limits_section(self):
        for skill in KNOWN_SKILLS:
            path = os.path.join(BASE, "skills", skill, "AGENT.md")
            with open(path) as f:
                content = f.read()
            assert "## LIMITS" in content, f"Missing LIMITS section in {skill}/AGENT.md"


# ===========================================================================
# CONFIG.yaml Validation Tests
# ===========================================================================

class TestConfigYaml:
    """Test CONFIG.yaml structure and content."""

    def _load_config(self, skill):
        path = os.path.join(BASE, "skills", skill, "CONFIG.yaml")
        with open(path) as f:
            return yaml.safe_load(f)

    def test_configs_parse_as_yaml(self):
        for skill in KNOWN_SKILLS:
            config = self._load_config(skill)
            assert config is not None
            assert isinstance(config, dict)

    def test_dreamer_config_has_skill_name(self):
        config = self._load_config("dreamer")
        assert config["skill"]["name"] == "dreamer"

    def test_dreamer_config_has_version(self):
        config = self._load_config("dreamer")
        assert "version" in config["skill"]
        assert config["skill"]["version"] != ""

    def test_dreamer_config_has_parameters(self):
        config = self._load_config("dreamer")
        assert "parameters" in config
        assert isinstance(config["parameters"], dict)

    def test_dreamer_config_has_strategies(self):
        config = self._load_config("dreamer")
        assert "dream_strategies" in config
        assert isinstance(config["dream_strategies"], list)
        assert len(config["dream_strategies"]) >= 3

    def test_dreamer_config_strategies_have_weights(self):
        config = self._load_config("dreamer")
        for strategy in config["dream_strategies"]:
            assert "name" in strategy
            assert "weight" in strategy
            assert 0.0 <= strategy["weight"] <= 1.0

    def test_streamer_config_has_templates(self):
        config = self._load_config("streamer")
        assert "templates" in config
        assert isinstance(config["templates"], list)

    def test_streamer_config_parameters(self):
        config = self._load_config("streamer")
        assert "parameters" in config
        assert "rate" in config["parameters"]
        assert "quality_threshold" in config["parameters"]

    def test_spreader_config_has_roles(self):
        config = self._load_config("spreader")
        assert "roles" in config
        assert isinstance(config["roles"], list)
        assert len(config["roles"]) == 6

    def test_spreader_roles_have_names(self):
        config = self._load_config("spreader")
        role_names = [r["name"] for r in config["roles"]]
        assert "architect" in role_names
        assert "critic" in role_names
        assert "pragmatist" in role_names
        assert "visionary" in role_names
        assert "historian" in role_names
        assert "contrarian" in role_names

    def test_spreader_config_has_synthesis(self):
        config = self._load_config("spreader")
        assert "synthesis" in config
        assert "consensus_threshold" in config["synthesis"]

    def test_mud_navigator_config_has_params(self):
        config = self._load_config("mud-navigator")
        assert "params" in config
        assert "mud_host" in config["params"]
        assert "mud_port" in config["params"]
        assert "agent_name" in config["params"]
        assert "agent_role" in config["params"]

    def test_mud_navigator_config_has_behavior(self):
        config = self._load_config("mud-navigator")
        assert "behavior" in config
        assert "on_enter" in config["behavior"]
        assert "on_idle" in config["behavior"]
        assert "on_message" in config["behavior"]

    def test_mud_navigator_config_has_instinct_map(self):
        config = self._load_config("mud-navigator")
        assert "instinct_map" in config
        assert isinstance(config["instinct_map"], dict)
        assert len(config["instinct_map"]) >= 5


# ===========================================================================
# Fluxasm File Structure Tests
# ===========================================================================

class TestFluxasmFiles:
    """Test .fluxasm file structure and content."""

    def _get_fluxasm_skills(self):
        """Get skills that have .fluxasm files."""
        result = []
        for skill in KNOWN_SKILLS:
            fluxasm_path = os.path.join(BASE, "skills", skill, f"{skill}.fluxasm")
            if os.path.exists(fluxasm_path):
                result.append((skill, fluxasm_path))
        return result

    def test_fluxasm_files_exist(self):
        fluxasm_skills = self._get_fluxasm_skills()
        assert len(fluxasm_skills) >= 3

    def test_fluxasm_files_not_empty(self):
        for skill, path in self._get_fluxasm_skills():
            with open(path) as f:
                content = f.read()
            assert len(content.strip()) > 0, f"{skill}.fluxasm is empty"

    def test_fluxasm_files_have_entry(self):
        for skill, path in self._get_fluxasm_skills():
            with open(path) as f:
                content = f.read()
            assert "ENTRY" in content or "entry" in content.lower() or "HALT" in content, \
                f"{skill}.fluxasm has no ENTRY or HALT"

    def test_dreamer_fluxasm_has_sections(self):
        path = os.path.join(BASE, "skills", "dreamer", "dreamer.fluxasm")
        with open(path) as f:
            content = f.read()
        assert "MARINATE" in content
        assert "ASSOCIATE" in content
        assert "FINISH" in content
        assert "STRATEGY" in content

    def test_streamer_fluxasm_has_sections(self):
        path = os.path.join(BASE, "skills", "streamer", "streamer.fluxasm")
        with open(path) as f:
            content = f.read()
        assert "STREAM" in content
        assert "GENERATE" in content
        assert "VALIDATE" in content
        assert "FINISH" in content

    def test_spreader_fluxasm_has_sections(self):
        path = os.path.join(BASE, "skills", "spreader", "spreader.fluxasm")
        with open(path) as f:
            content = f.read()
        assert "DISPATCH" in content
        assert "ANALYZE_ROLE" in content
        assert "SYNTHESIZE" in content
        assert "ROLE_PROMPT" in content

    def test_mud_navigator_fluxasm_has_phases(self):
        path = os.path.join(BASE, "skills", "mud-navigator", "mud_navigator.fluxasm")
        with open(path) as f:
            content = f.read()
        assert "INIT" in content or "Initialize" in content
        assert "HALT" in content


# ===========================================================================
# Skills Registry Tests
# ===========================================================================

class TestSkillsRegistry:
    """Test the SKILLS-REGISTRY.md file."""

    def test_registry_exists(self):
        path = os.path.join(BASE, "SKILLS-REGISTRY.md")
        assert os.path.exists(path)

    def test_registry_lists_skills(self):
        path = os.path.join(BASE, "SKILLS-REGISTRY.md")
        with open(path) as f:
            content = f.read()
        assert "spreader" in content
        assert "dreamer" in content
        assert "streamer" in content

    def test_registry_has_descriptions(self):
        path = os.path.join(BASE, "SKILLS-REGISTRY.md")
        with open(path) as f:
            content = f.read()
        # Each skill entry should have a description
        for skill in ["spreader", "dreamer", "streamer"]:
            assert len(content.split(skill)[1].split("\n")[0].strip()) > 0


# ===========================================================================
# Repository Structure Tests
# ===========================================================================

class TestRepoStructure:
    """Test overall repository structure."""

    def test_readme_exists(self):
        path = os.path.join(BASE, "README.md")
        assert os.path.exists(path)

    def test_license_exists(self):
        path = os.path.join(BASE, "LICENSE")
        assert os.path.exists(path)

    def test_runtime_directory_exists(self):
        path = os.path.join(BASE, "runtime")
        assert os.path.isdir(path)

    def test_skills_directory_exists(self):
        path = os.path.join(BASE, "skills")
        assert os.path.isdir(path)

    def test_docs_directory_exists(self):
        path = os.path.join(BASE, "docs")
        assert os.path.isdir(path)

    def test_skill_vm_exists(self):
        path = os.path.join(BASE, "runtime", "skill_vm.py")
        assert os.path.exists(path)

    def test_conformance_exists(self):
        path = os.path.join(BASE, "runtime", "conformance.py")
        assert os.path.exists(path)

    def test_abstraction_md_exists(self):
        path = os.path.join(BASE, "ABSTRACTION.md")
        assert os.path.exists(path)

    def test_docs_have_required_files(self):
        for doc in ["A2A-DOC-SPEC.md", "COMPOSITION.md", "MODIFICATION.md"]:
            path = os.path.join(BASE, "docs", doc)
            assert os.path.exists(path), f"Missing docs/{doc}"

    def test_readme_mentions_flux_vm(self):
        path = os.path.join(BASE, "README.md")
        with open(path) as f:
            content = f.read()
        assert "FLUX" in content or "flux" in content

    def test_readme_mentions_skills(self):
        path = os.path.join(BASE, "README.md")
        with open(path) as f:
            content = f.read()
        assert "skill" in content.lower()

    def test_readme_mentions_bytecode(self):
        path = os.path.join(BASE, "README.md")
        with open(path) as f:
            content = f.read()
        assert "bytecode" in content.lower()
