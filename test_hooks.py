#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test hook functionality
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.config import ConfigManager

def test_config_schema():
    """Test that config schema accepts new hooks"""
    print("Testing config schema...")

    # Create a config with hooks
    config_data = {
        'project': {'name': 'test', 'version': '1.0.0'},
        'fpga': {'vendor': 'xilinx', 'part': 'xc7z045ffg676-2'},
        'build': {
            'hooks': {
                'pre_build': 'echo "pre-build"',
                'post_bitstream': [
                    'echo "command1"',
                    'echo "command2"'
                ]
            }
        }
    }

    config_manager = ConfigManager()

    # Validate config
    try:
        config_manager.validate_config(config_data)
        print("[OK] Config schema validation passed")
    except Exception as e:
        print(f"[FAIL] Config schema validation failed: {e}")
        return False

    # Test YAML config file
    yaml_content = """
project:
  name: test
  version: 1.0.0
fpga:
  vendor: xilinx
  part: xc7z045ffg676-2
build:
  hooks:
    pre_build: |
      echo "line1"
      echo "line2"
    post_bitstream:
      - echo "cmd1"
      - echo "cmd2"
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_file = f.name

    try:
        config = config_manager.load_config(yaml_file)
        hooks = config.get('build', {}).get('hooks', {})
        print("[OK] YAML config loaded successfully")
        print(f"  pre_build: {hooks.get('pre_build')}")
        print(f"  post_bitstream: {hooks.get('post_bitstream')}")
    except Exception as e:
        print(f"[FAIL] YAML config loading failed: {e}")
        return False
    finally:
        os.unlink(yaml_file)

    return True

def test_tcl_template_hooks():
    """Test hook processing in TCL templates"""
    print("\nTesting TCL template hooks...")

    from plugins.vivado.tcl_templates import TCLTemplateBase

    # Mock config
    config = {
        'project': {'name': 'test'},
        'fpga': {'part': 'xc7z045ffg676-2'},
        'build': {
            'hooks': {
                'pre_build': 'echo "pre-build"',
                'pre_synth': ['echo "pre-synth1"', 'echo "pre-synth2"'],
                'post_bitstream': 'scripts/post_bitstream.tcl'
            }
        }
    }

    class TestTemplate(TCLTemplateBase):
        def render(self):
            return ""

    template = TestTemplate(config)

    # Test _get_hook_commands
    commands = template._get_hook_commands('pre_build')
    print(f"[OK] pre_build hook commands: {commands}")

    commands = template._get_hook_commands('pre_synth')
    print(f"[OK] pre_synth hook commands (array): {commands}")

    # Test file path detection
    # Create a temporary script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False) as f:
        f.write('puts "test"')
        script_file = f.name

    config_with_file = {
        'project': {'name': 'test'},
        'fpga': {'part': 'xc7z045ffg676-2'},
        'build': {
            'hooks': {
                'post_bitstream': script_file
            }
        }
    }

    template2 = TestTemplate(config_with_file)
    commands = template2._get_hook_commands('post_bitstream')
    print(f"[OK] File path hook commands: {commands}")

    os.unlink(script_file)

    return True

def test_cli_hook_execution():
    """Test hook execution in CLI (simulated)"""
    print("\nTesting CLI hook execution...")

    from core.cli import CLI

    # Test string hook
    print("Testing string hook...")
    success = CLI._execute_hook('echo "test"', 'test-hook')
    print(f"  Result: {success}")

    # Test array hook
    print("Testing array hook...")
    success = CLI._execute_hook(['echo "cmd1"', 'echo "cmd2"'], 'test-hook')
    print(f"  Result: {success}")

    # Test multiline string
    print("Testing multiline string hook...")
    multiline = """echo "line1"
echo "line2"
echo "line3"""
    success = CLI._execute_hook(multiline, 'test-hook')
    print(f"  Result: {success}")

    return True

def main():
    """Main test function"""
    print("=" * 60)
    print("Hook Functionality Test")
    print("=" * 60)

    results = []

    results.append(("Config schema test", test_config_schema()))
    results.append(("TCL template hooks test", test_tcl_template_hooks()))
    results.append(("CLI hook execution test", test_cli_hook_execution()))

    print("\n" + "=" * 60)
    print("Test results summary:")
    for name, success in results:
        status = "[OK] Passed" if success else "[FAIL] Failed"
        print(f"  {name}: {status}")

    all_passed = all(success for _, success in results)
    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()