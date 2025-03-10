import os
import sys
import subprocess
import platform

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

GODOT_DIR = os.path.join(BASE_DIR, "godot")
GODOT_CPP_DIR = os.path.join(BASE_DIR, "godot-cpp")
SWIFT_GODOT_DIR = os.path.join(BASE_DIR, "SwiftGodot")
SWIFT_GODOT_KIT_DIR = os.path.join(BASE_DIR, "SwiftGodotKit")
BUILD_DIR = os.path.join(BASE_DIR, "build")

host_system = platform.uname().system
host_arch = platform.uname().machine
host_target = "editor"
target = "editor"
target_arch = ""
precision = "double"
host_build_options = " precision={}".format(precision)
target_build_options = " precision={}".format(precision)

if precision == "single":
    host_build_options = " "
    target_build_options = " "

lib_suffix = "so"
host_debug = 1
debug = 1
force_regenerate = 1

if host_system == 'Linux':
    host_platform = "linuxbsd"
    cpus = os.cpu_count()
    target_platform = "linuxbsd"
elif host_system == 'Windows':
    host_platform = "windows"
    cpus = os.cpu_count()
    target_platform = "windows"
    host_arch = "x86_64"
    lib_suffix = "dll"
elif host_system == 'Darwin':
    host_platform = "macos"
    cpus = os.cpu_count()
    target_platform = "macos"
    lib_suffix = "dylib"
else:
    print(f"System {host_system} is unsupported")
    sys.exit(1)

args = sys.argv[1:]
while args:
    arg = args.pop(0)
    if arg == "--host-debug":
        host_debug = 1
    elif arg == "--regenerate":
        force_regenerate = 1
    elif arg == "--debug":
        debug = 1
    elif arg == "--target":
        target_platform = args.pop(0)
    else:
        print(f"Usage: {sys.argv[0]} [--host-debug] [--host-rebuild] [--debug] [--regenerate] --target <target platform>")
        sys.exit(1)

if target_platform == "ios":
    target_arch = "arm64"
    target = "template_debug"
    lib_suffix = "a"

if not target_arch:
    target_arch = host_arch

host_godot_suffix = f"{host_platform}.{host_target}"
target_godot_suffix = f"{target_platform}.{target}"

if host_debug == 1:
    host_build_options += " dev_build=yes"
    host_godot_suffix += ".dev"

if debug == 1:
    target_build_options += " dev_build=yes"
    target_godot_suffix += ".dev"

if precision == "double":
    host_godot_suffix += ".double"
    target_godot_suffix += ".double"

host_godot_suffix += f".{host_arch}"
target_godot_suffix += f".{target_arch}"

host_godot = os.path.join(GODOT_DIR, "bin", f"godot.{host_godot_suffix}")
target_godot = os.path.join(GODOT_DIR, "bin", f"libgodot.{target_godot_suffix}.{lib_suffix}")

if os.path.exists(host_godot):
    os.remove(host_godot)
command = "scons"
platform = f"{host_platform}"
target = f"{host_target}"
options = host_build_options.split()
run_args = [command, f"platform={target_platform}", f"target={target}", "library_type=executable"] + options
subprocess.run(run_args, cwd=GODOT_DIR)

os.makedirs(BUILD_DIR, exist_ok=True)
if not os.path.isfile(os.path.join(BUILD_DIR, "extension_api.json")) or force_regenerate == 1:
    subprocess.run([host_godot, "--dump-extension-api"], cwd=BUILD_DIR)
subprocess.run(["scons", f"platform={target_platform}", f"target={target}"] + options + ["library_type=shared_library"], cwd=GODOT_DIR)
subprocess.run(["cp", "-v", target_godot, os.path.join(BUILD_DIR, f"libgodot.{lib_suffix}")], cwd=GODOT_DIR)

subprocess.run(["cp", "-v", os.path.join(BUILD_DIR, "extension_api.json"), os.path.join(GODOT_CPP_DIR, "gdextension")], cwd=GODOT_DIR)
subprocess.run(["cp", "-v", os.path.join(GODOT_DIR, "core", "extension", "gdextension_interface.h"), os.path.join(GODOT_CPP_DIR, "gdextension")], cwd=GODOT_DIR)

subprocess.run(
    [
        "scons",
        f"platform={target_platform}",
        f"target={target}",
        f"precision={precision}",
        f"arch={target_arch}",
    ],
    cwd=GODOT_CPP_DIR,
    check=True
)

godot_cpp_lib_name = f"libgodot-cpp.{target_platform}.{target}.{target_arch}.a"
if precision == "double":
    godot_cpp_lib_name += ".double"
if debug == 1:
    godot_cpp_lib_name += ".dev"

godot_cpp_source = os.path.join(GODOT_CPP_DIR, "bin", godot_cpp_lib_name)
godot_cpp_dest = os.path.join(GODOT_CPP_DIR, "bin", "libgodot-cpp.a")

if not os.path.exists(godot_cpp_source):
    print(f"Error: Source file not found - {godot_cpp_source}")
    print("Possible causes:")
    print(f"1. Verify target platform '{target_platform}' and architecture '{target_arch}' are correct")
    print(f"2. Check build parameters: target={target}, precision={precision}, debug={debug}")
    sys.exit(1)

try:
    subprocess.run(
        ["cp", "-v", godot_cpp_source, godot_cpp_dest],
        cwd=GODOT_DIR,
        check=True
    )
except subprocess.CalledProcessError as e:
    print(f"Copy failed with error: {e}")
    sys.exit(1)

godot_cpp_lib_name = f"libgodot-cpp.{target_platform}.{target}.{target_arch}.a"
godot_cpp_source = os.path.join(GODOT_CPP_DIR, "bin", godot_cpp_lib_name)
godot_cpp_dest = os.path.join(GODOT_CPP_DIR, "bin", "libgodot-cpp.a")

subprocess.run(["cp", "-v", godot_cpp_source, godot_cpp_dest], cwd=GODOT_DIR)

zig_out_bin = os.path.join("godot-zig", "zig-out", "bin")
os.makedirs(zig_out_bin, exist_ok=True)
subprocess.run(["cp", "-v", os.path.join(BUILD_DIR, f"libgodot.{lib_suffix}"), os.path.join(BUILD_DIR, "..", zig_out_bin, f"libgodot.{lib_suffix}")], cwd=GODOT_DIR)

if target_platform == "ios":
    subprocess.run([os.path.join(SWIFT_GODOT_DIR, "scripts", "make-libgodot.framework"), GODOT_DIR, BUILD_DIR], cwd=GODOT_DIR)
    subprocess.run(["cp", "-v", os.path.join(BUILD_DIR, "extension_api.json"), os.path.join(SWIFT_GODOT_DIR, "Sources", "ExtensionApi")], cwd=GODOT_DIR)
    subprocess.run(["cp", "-v", os.path.join(GODOT_DIR, "core", "extension", "gdextension_interface.h"), os.path.join(SWIFT_GODOT_DIR, "Sources", "GDExtension", "include")], cwd=GODOT_DIR)
