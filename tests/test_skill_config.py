"""Tests for skill configuration loading and validation."""
import pytest
import os
import yaml


class TestSkillConfigLoading:
    """Test that all skill CONFIG.yaml files are valid and loadable."""

    SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")

    def get_skill_dirs(self):
        if not os.path.exists(self.SKILLS_DIR):
            return []
        return [d for d in os.listdir(self.SKILLS_DIR)
                if os.path.isdir(os.path.join(self.SKILLS_DIR, d))]

    def test_all_skills_have_config(self):
        """Every skill directory should have a CONFIG.yaml."""
        for skill in self.get_skill_dirs():
            config_path = os.path.join(self.SKILLS_DIR, skill, "CONFIG.yaml")
            assert os.path.exists(config_path), f"{skill} missing CONFIG.yaml"

    def test_all_skills_have_agent_md(self):
        """Every skill directory should have an AGENT.md."""
        for skill in self.get_skill_dirs():
            agent_path = os.path.join(self.SKILLS_DIR, skill, "AGENT.md")
            assert os.path.exists(agent_path), f"{skill} missing AGENT.md"

    def test_streamer_config_loads(self):
        config_path = os.path.join(self.SKILLS_DIR, "streamer", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["skill"]["name"] == "streamer"
        assert config["skill"]["version"] == "1.0.0"
        assert "parameters" in config
        assert config["parameters"]["rate"] == 10
        assert config["parameters"]["quality_threshold"] == 0.8

    def test_dreamer_config_loads(self):
        config_path = os.path.join(self.SKILLS_DIR, "dreamer", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["skill"]["name"] == "dreamer"
        assert "dream_strategies" in config
        assert len(config["dream_strategies"]) == 5

    def test_spreader_config_loads(self):
        config_path = os.path.join(self.SKILLS_DIR, "spreader", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["skill"]["name"] == "spreader"
        assert "roles" in config
        assert len(config["roles"]) == 6
        assert "synthesis" in config
        assert config["synthesis"]["consensus_threshold"] == 0.7

    def test_murmur_config_loads(self):
        config_path = os.path.join(self.SKILLS_DIR, "murmur", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["meta"]["skill_name"] == "murmur"
        assert config["provider"]["type"] == "none"
        assert config["runtime"]["max_iterations"] == 1000

    def test_mud_navigator_config_loads(self):
        config_path = os.path.join(self.SKILLS_DIR, "mud-navigator", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["name"] == "mud-navigator"
        assert config["runtime"] == "flux-vm"
        assert "params" in config
        assert config["params"]["mud_port"] == 7777

    def test_streamer_templates(self):
        config_path = os.path.join(self.SKILLS_DIR, "streamer", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        templates = config.get("templates", [])
        assert len(templates) == 4
        names = [t["name"] for t in templates]
        assert "conformance_vector" in names
        assert "test_case" in names
        assert "doc_entry" in names
        assert "readme_section" in names

    def test_dreamer_strategies_have_weights(self):
        config_path = os.path.join(self.SKILLS_DIR, "dreamer", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        for strategy in config["dream_strategies"]:
            assert "name" in strategy
            assert "weight" in strategy
            assert 0.0 <= strategy["weight"] <= 1.0

    def test_spreader_roles_have_prompts(self):
        config_path = os.path.join(self.SKILLS_DIR, "spreader", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        for role in config["roles"]:
            assert "name" in role
            assert "prompt" in role
            assert "weight" in role

    def test_murmur_strategies(self):
        config_path = os.path.join(self.SKILLS_DIR, "murmur", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        strategies = config["behavior"]["strategies"]
        expected = ["explore", "connect", "contradict", "synthesize", "question"]
        assert strategies == expected

    def test_mud_navigator_instinct_map(self):
        config_path = os.path.join(self.SKILLS_DIR, "mud-navigator", "CONFIG.yaml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        instincts = config.get("instinct_map", config.get("behavior", {}).get("instinct_map", {}))
        assert "explore" in instincts
        assert "socialize" in instincts
        assert "teach" in instincts
        assert len(instincts) == 10


class TestAgentMDStructure:
    """Verify AGENT.md files follow the skill spec."""

    SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")

    REQUIRED_SECTIONS = ["WHAT", "WHY", "HOW", "INPUT", "OUTPUT", "CONFIG", "MODIFY", "COMPOSE", "FEEDBACK", "LIMITS"]

    def test_agent_md_has_required_sections(self):
        skills = [d for d in os.listdir(self.SKILLS_DIR)
                  if os.path.isdir(os.path.join(self.SKILLS_DIR, d))]
        for skill in skills:
            agent_path = os.path.join(self.SKILLS_DIR, skill, "AGENT.md")
            with open(agent_path) as f:
                content = f.read()
            for section in self.REQUIRED_SECTIONS:
                assert section in content, f"{skill}/AGENT.md missing section: {section}"

    def test_streamer_agent_md_content(self):
        agent_path = os.path.join(self.SKILLS_DIR, "streamer", "AGENT.md")
        with open(agent_path) as f:
            content = f.read()
        assert "continuous" in content.lower() or "stream" in content.lower()
        assert "Streamer" in content

    def test_dreamer_agent_md_content(self):
        agent_path = os.path.join(self.SKILLS_DIR, "dreamer", "AGENT.md")
        with open(agent_path) as f:
            content = f.read()
        assert "dream" in content.lower()
        assert "connection" in content.lower()

    def test_spreader_agent_md_content(self):
        agent_path = os.path.join(self.SKILLS_DIR, "spreader", "AGENT.md")
        with open(agent_path) as f:
            content = f.read()
        assert "perspective" in content.lower()
        assert "synthesis" in content.lower()
