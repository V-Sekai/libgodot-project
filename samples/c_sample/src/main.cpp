#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gdextension_interface.h>

#include <godot_cpp/classes/godot_instance.hpp>
#include <godot_cpp/core/defs.hpp>
#include <godot_cpp/godot.hpp>

extern "C" {

static void
initialize_default_module(godot::ModuleInitializationLevel p_level) {
  if (p_level != godot::MODULE_INITIALIZATION_LEVEL_SCENE) {
    return;
  }
}

static void
uninitialize_default_module(godot::ModuleInitializationLevel p_level) {
  if (p_level != godot::MODULE_INITIALIZATION_LEVEL_SCENE) {
    return;
  }
}

GDExtensionBool GDE_EXPORT
gdextension_default_init(GDExtensionInterfaceGetProcAddress p_get_proc_address,
                         GDExtensionClassLibraryPtr p_library,
                         GDExtensionInitialization *r_initialization) {
  godot::GDExtensionBinding::InitObject init_object(
      p_get_proc_address, p_library, r_initialization);

  init_object.register_initializer(initialize_default_module);
  init_object.register_terminator(uninitialize_default_module);
  init_object.set_minimum_library_initialization_level(
      godot::MODULE_INITIALIZATION_LEVEL_SCENE);

  return init_object.init();
}

#ifdef _WIN32
#include <windows.h>
char *dlerror() {
  static char buf[256];
  FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
                NULL, GetLastError(), MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                buf, sizeof(buf), NULL);
  return buf;
}
#define dlopen(x, y) LoadLibrary(x)
#define dlsym(x, y) GetProcAddress((HMODULE)x, y)
#define dlclose(x) FreeLibrary((HMODULE)x)
#else
#include <dlfcn.h>
#endif

#include <gdextension_interface.h>

#ifdef _WIN32
#define LIBGODOT_LIBRARY_NAME "libgodot.dll"
#else
#ifdef __APPLE__
#define LIBGODOT_LIBRARY_NAME "libgodot.dylib"
#else
#define LIBGODOT_LIBRARY_NAME "./libgodot.so"
#endif
#endif

typedef struct {
  void *handle;
  GDExtensionObjectPtr (*func_libgodot_create_godot_instance)(
      int, char *[], GDExtensionInitializationFunction);
} LibGodot;

static int run_godot_instance(LibGodot *libgodot, int argc, char *argv[],
                              GDExtensionInitializationFunction init_func) {
  if (libgodot == NULL) {
    fprintf(stderr, "Error: LibGodot is NULL\n");
    return EXIT_FAILURE;
  }

  GDExtensionObjectPtr instance =
      libgodot->func_libgodot_create_godot_instance(argc, argv, init_func);
  if (instance == NULL) {
    fprintf(stderr, "Error creating Godot instance\n");
    return EXIT_FAILURE;
  }

  godot::GodotInstance *godot_instance =
      reinterpret_cast<godot::GodotInstance *>(
          godot::internal::get_object_instance_binding(instance));
  godot_instance->start();

  while (!godot_instance->iteration()) {
  }

  godot_instance->stop();

  return EXIT_SUCCESS;
}

LibGodot *libgodot_new(const char *p_path) {
  LibGodot *self = (LibGodot *)malloc(sizeof(LibGodot));
  self->handle = dlopen(p_path, RTLD_LAZY);
  if (self->handle == NULL) {
    fprintf(stderr, "Error opening libgodot: %s\n", dlerror());
    free(self);
    return NULL;
  }
  self->func_libgodot_create_godot_instance = (GDExtensionObjectPtr(*)(
      int, char *[], GDExtensionInitializationFunction))
      dlsym(self->handle, "libgodot_create_godot_instance");
  if (self->func_libgodot_create_godot_instance == NULL) {
    fprintf(stderr, "Error acquiring function: %s\n", dlerror());
    dlclose(self->handle);
    free(self);
    return NULL;
  }
  return self;
}

void libgodot_delete(LibGodot *self) {
  if (self != NULL) {
    if (self->handle != NULL) {
      dlclose(self->handle);
    }
    free(self);
  }
}

int main(int argc, char **argv) {

  LibGodot *libgodot = libgodot_new(LIBGODOT_LIBRARY_NAME);

  char *program = NULL;
  if (argc > 0) {
    program = argv[0];
  }

  char path_arg[] = "--path";
  char project_path[] = "../../project/";
  char editor[] = "-e";

  char *instance_args[] = {program, path_arg, project_path, editor, NULL};

  int instance_argc = 0;
  while (instance_args[instance_argc] != NULL) {
    instance_argc++;
  }

  int exit_code = run_godot_instance(libgodot, instance_argc, instance_args,
                                     gdextension_default_init);

  libgodot_delete(libgodot);

  return exit_code;
}
}
