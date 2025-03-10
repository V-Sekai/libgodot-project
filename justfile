base_dir := `pwd`
build_dir := join(base_dir, "build")
scons_cache_dir := join(build_dir, "scons_cache")

host_system := os()
host_arch := arch()

host_platform := if host_system == "linux" {
  "linuxbsd"
} else if host_system == "macos" {
  "macos"
} else if host_system == "windows" {
  "windows"
} else {
  error("Unsupported system: " + host_system)
}

target_platform := host_platform
target_arch := if host_arch == "arm64" { "arm64" } else { "x86_64" }
precision := "double"
lib_suffix := if host_system == "macos" { "dylib" } else if host_system == "windows" { "dll" } else { "so" }
target := if target_platform == "ios" { "template_debug" } else { "editor" }

godot_dir := join(base_dir, "godot")
godot_cpp_dir := join(base_dir, "godot-cpp")
swift_godot_dir := join(base_dir, "SwiftGodot")

host_build_options := if precision == "double" { "precision=double" } else { "" }
target_build_options := host_build_options

build: build_host generate_headers build_target build_godot_cpp copy_files
  @echo "Build complete"

build_host:
  #!/usr/bin/env bash
  mkdir -p {{scons_cache_dir}}
  export SCONS_CACHE={{scons_cache_dir}}
  cd {{godot_dir}} && \
  scons platform={{host_platform}} target=editor {{host_build_options}} library_type=executable

build_target:
  #!/usr/bin/env bash
  mkdir -p {{scons_cache_dir}}
  export SCONS_CACHE={{scons_cache_dir}}
  cd {{godot_dir}} && \
  scons platform={{target_platform}} target={{target}} {{target_build_options}} library_type=shared_library

generate_headers:
  #!/usr/bin/env bash
  mkdir -p {{build_dir}}
  {{godot_dir}}/bin/godot.* --dump-extension-api --headless
  cp -v {{build_dir}}/extension_api.json {{godot_cpp_dir}}/gdextension/
  cp -v {{godot_dir}}/core/extension/gdextension_interface.h {{godot_cpp_dir}}/gdextension/

build_godot_cpp:
  #!/usr/bin/env bash
  mkdir -p {{scons_cache_dir}}
  export SCONS_CACHE={{scons_cache_dir}}
  cd {{godot_cpp_dir}} && \
  scons platform={{target_platform}} target={{target}} precision={{precision}} arch={{target_arch}}
  
  lib_name="libgodot-cpp.{{target_platform}}.{{target}}"
  [[ "{{precision}}" == "double" ]] && lib_name+=".double"
  lib_name+=".{{target_arch}}.a"
  
  src="{{godot_cpp_dir}}/bin/${lib_name}"
  dest="{{godot_cpp_dir}}/bin/libgodot-cpp.a"
  
  if [ ! -f "$src" ]; then
    echo "Missing built library: $src"
    exit 1
  fi
  cp -v "$src" "$dest"

copy_files:
  #!/usr/bin/env bash
  mkdir -p {{build_dir}}
  cp -v {{godot_dir}}/bin/libgodot.* {{build_dir}}/libgodot.{{lib_suffix}}
  
  zig_bin="{{base_dir}}/godot-zig/zig-out/bin"
  mkdir -p "$zig_bin"
  cp -v {{build_dir}}/libgodot.{{lib_suffix}} "$zig_bin/"

build_ios:
  just build target_platform=ios target_arch=arm64 lib_suffix=a
  #!/usr/bin/env bash
  {{swift_godot_dir}}/scripts/make-libgodot.framework {{godot_dir}} {{build_dir}}
  cp -v {{build_dir}}/extension_api.json {{swift_godot_dir}}/Sources/ExtensionApi/
  cp -v {{godot_dir}}/core/extension/gdextension_interface.h {{swift_godot_dir}}/Sources/GDExtension/include/

clean:
  #!/usr/bin/env bash
  cd {{godot_dir}} && scons --clean
  cd {{godot_cpp_dir}} && scons --clean

print_config:
  @echo "Build Configuration:"
  @echo "Host System: {{host_system}}"
  @echo "Target Platform: {{target_platform}}"
  @echo "Architecture: {{target_arch}}"
  @echo "Precision: {{precision}}"
