import platform
import os
from pathlib import Path
from SCons.Script import *

num_cores = os.cpu_count() or 1
SetOption('num_jobs', num_cores)

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
    TARGET_PLATFORM=GetOption('target'),
    REGENERATE=GetOption('regenerate'),
    PRECISION=GetOption('precision')
)

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
    'template_release',
    'double' if env['PRECISION'] == 'double' else 'single'
])

def build_godot(env, target, source):
    cmd = [
        "scons",
        f"platform={env['TARGET_PLATFORM']}",
        f"target=template_release",
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

godot_bin_path = env['GODOT_DIR'] / 'bin' / f"godot.windows.template_release.{'double' if env['PRECISION'] == 'double' else 'single'}.x86_64.exe"
godot_bin = build_godot(
    env,
    target=godot_bin_path,
    source=env['GODOT_DIR'] / "SConstruct"
)

api_file = generate_api(
    env,
    target=BUILD_DIR / "extension_api.json",
    source=godot_bin_path
)

cpp_lib = env.Command(
    target=BUILD_DIR / "libgodot-cpp.a",
    source=[],
    action=[
        [
            "scons",
            "generate_bindings=yes",
            f"platform={env['TARGET_PLATFORM']}",
            f"precision={env['PRECISION']}",
            f"-j{env.GetOption('num_jobs')}"
        ]
    ],
    chdir=str(env['GODOT_CPP_DIR'])
)

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

Default(godot_bin, cpp_lib)
