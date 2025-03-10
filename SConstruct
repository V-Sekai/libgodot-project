import platform
import os
from pathlib import Path
from SCons.Script import *

BASE_DIR = Path(os.getcwd()).resolve()
BUILD_DIR = BASE_DIR / "build"

host_system = platform.system()
system_map = {
    'Linux': 'linuxbsd',
    'Windows': 'windows',
    'Darwin': 'macos'
}
host_platform = system_map.get(host_system, 'linuxbsd')

AddOption('--target', dest='target', type='string', default=host_platform)
AddOption('--regenerate', dest='regenerate', action='store_true', default=False)
AddOption('--precision', dest='precision', type='string', default='double')

env = Environment(
    ENV=os.environ,
    BASE_DIR=BASE_DIR,
    BUILD_DIR=BUILD_DIR,
    GODOT_DIR=BASE_DIR / 'godot',
    GODOT_CPP_DIR=BASE_DIR / 'godot-cpp',
    SWIFT_DIR=BASE_DIR / 'SwiftGodot',
    TARGET_PLATFORM=GetOption('target'),  # Renamed from TARGET to TARGET_PLATFORM
    REGENERATE=GetOption('regenerate'),
    PRECISION=GetOption('precision')
)

# Platform-specific configurations
env['LIB_SUFFIX'] = 'so'
if env['TARGET_PLATFORM'] == 'windows':
    env['LIB_SUFFIX'] = 'dll'
    env.Append(ENV={'PATH': os.environ['PATH']})
elif env['TARGET_PLATFORM'] == 'macos':
    env['LIB_SUFFIX'] = 'dylib'
elif env['TARGET_PLATFORM'] == 'ios':
    env['LIB_SUFFIX'] = 'a'

env['BUILD_SUFFIX'] = '.'.join([
    env['TARGET_PLATFORM'],
    'editor',
    'double' if env['PRECISION'] == 'double' else 'single'
])

def build_godot(env, target, source):
    cmd = [
        "scons",
        f"platform={env['TARGET_PLATFORM']}",
        f"target={'template_release'}",
        f"precision={env['PRECISION']}",
        f"-j{env.GetOption('num_jobs')}"
    ]
    return env.Command(
        target=target,
        source=source,
        action=[cmd],
        chdir=str(env['GODOT_DIR'])
    )

def generate_api(env, target, source):
    return env.Command(
        target=target,
        source=source,
        action=f"$SOURCE --dump-extension-api $TARGET",
        chdir=str(BUILD_DIR)
    )

# Build targets
godot_bin = build_godot(
    env,
    target=BUILD_DIR / f"godot.{env['BUILD_SUFFIX']}",
    source=env['GODOT_DIR'] / "SConstruct"
)

api_file = generate_api(
    env,
    target=BUILD_DIR / "extension_api.json",
    source=godot_bin
)

# File copy actions
api_copy = env.Command(
    target=env['GODOT_CPP_DIR'] / "gdextension/extension_api.json",
    source=api_file,
    action=Copy("$TARGET", "$SOURCE")
)

header_copy = env.Command(
    target=env['GODOT_CPP_DIR'] / "gdextension/gdextension_interface.h",
    source=env['GODOT_DIR'] / "core/extension/gdextension_interface.h",
    action=Copy("$TARGET", "$SOURCE")
)

# Godot-cpp build
cpp_lib = env.Command(
    target=BUILD_DIR / "libgodot-cpp.a",
    source=[api_copy, header_copy],
    action=[
        f"scons generate_bindings=yes platform={env['TARGET_PLATFORM']} "
        f"precision={env['PRECISION']} -j{env.GetOption('num_jobs')}"
    ],
    chdir=str(env['GODOT_CPP_DIR'])
)

# SwiftGodot integration
if env['TARGET_PLATFORM'] == 'ios':
    swift_framework = env.Command(
        target=BUILD_DIR / "libgodot.framework",
        source=[
            env['SWIFT_DIR'] / "scripts/make-libgodot.framework",
            godot_bin,
            cpp_lib
        ],
        action=f"$SOURCE {env['GODOT_DIR']} {BUILD_DIR}",
        chdir=str(env['SWIFT_DIR'])
    )
    Default(swift_framework)

# Main build
Default(godot_bin, cpp_lib)
