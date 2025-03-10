import argparse
import platform
import shutil
import subprocess
import sys
import os
from pathlib import Path

def main():
    BASE_DIR = Path(__file__).parent.resolve()
    DIRS = {
        'godot': BASE_DIR / "godot",
        'godot-cpp': BASE_DIR / "godot-cpp",
        'swiftgodot': BASE_DIR / "SwiftGodot",
        'build': BASE_DIR / "build",
        'zig_out': BASE_DIR / "godot-zig" / "zig-out" / "bin"
    }

    SYSTEM_MAP = {
        'Linux': 'linuxbsd',
        'Windows': 'windows',
        'Darwin': 'macos'
    }
    host_system = platform.system()
    host_platform = SYSTEM_MAP[host_system]
    host_arch = platform.machine() or 'x86_64'

    config = {
        'precision': 'double',
        'debug': True,
        'force_regenerate': False,
        'cpus': os.cpu_count() or 4,
        'lib_suffix': 'so',
        'target_arch': host_arch
    }

    parser = argparse.ArgumentParser(description="Godot Engine Build System")
    parser.add_argument("--target", required=True, choices=SYSTEM_MAP.values(),
                        help="Target platform for compilation")
    parser.add_argument("--debug", action="store_true", 
                       help="Build with debug symbols")
    parser.add_argument("--regenerate", action="store_true",
                       help="Force regeneration of API files")
    args = parser.parse_args()

    config.update({
        'debug': args.debug,
        'force_regenerate': args.regenerate,
        'target_platform': args.target
    })

    if host_system == 'Windows':
        config['lib_suffix'] = 'dll'
    elif host_system == 'Darwin':
        config['lib_suffix'] = 'dylib'

    if config['target_platform'] == 'ios':
        config.update({
            'target_arch': 'arm64',
            'lib_suffix': 'a'
        })

    build_suffix = f"{config['target_platform']}.{config['target_arch']}"
    if config['debug']:
        build_suffix += ".dev"
    if config['precision'] == 'double':
        build_suffix += ".double"

    # Path definitions
    godot_bin = DIRS['godot'] / "bin"
    host_godot = godot_bin / f"godot.{host_platform}.editor.{build_suffix}"
    target_godot = godot_bin / f"libgodot.{build_suffix}.{config['lib_suffix']}"

    try:
        if host_godot.exists():
            host_godot.unlink()

        build_command = [
            "scons",
            f"platform={host_platform}",
            "target=editor",
            "library_type=executable",
            f"precision={config['precision']}",
            f"-j{config['cpus']}"
        ]
        subprocess.run(build_command, cwd=DIRS['godot'], check=True)

        DIRS['build'].mkdir(exist_ok=True)
        api_file = DIRS['build'] / "extension_api.json"

        if not api_file.exists() or config['force_regenerate']:
            subprocess.run([str(host_godot), "--dump-extension-api"], 
                          cwd=DIRS['build'], check=True)

        subprocess.run([
            "scons",
            f"platform={config['target_platform']}",
            "target=editor",
            "library_type=shared_library",
            f"precision={config['precision']}",
            f"-j{config['cpus']}"
        ], cwd=DIRS['godot'], check=True)

        shutil.copy(target_godot, DIRS['build'] / f"libgodot.{config['lib_suffix']}")
        shutil.copy(api_file, DIRS['godot-cpp'] / "gdextension")
        
        header_src = DIRS['godot'] / "core" / "extension" / "gdextension_interface.h"
        header_dest = DIRS['godot-cpp'] / "gdextension"
        shutil.copy(header_src, header_dest)

        subprocess.run([
            "scons",
            f"platform={config['target_platform']}",
            "target=editor",
            f"precision={config['precision']}",
            f"arch={config['target_arch']}",
            f"-j{config['cpus']}"
        ], cwd=DIRS['godot-cpp'], check=True)

        if config['target_platform'] == 'ios':
            framework_script = DIRS['swiftgodot'] / "scripts" / "make-libgodot.framework"
            subprocess.run([str(framework_script), str(DIRS['godot']), str(DIRS['build'])], check=True)
            shutil.copy(api_file, DIRS['swiftgodot'] / "Sources" / "ExtensionApi")
            swift_header_dir = DIRS['swiftgodot'] / "Sources" / "GDExtension" / "include"
            shutil.copy(header_src, swift_header_dir)

        print("\nBuild completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
