/**************************************************************************/
/*  rendering_native_surface_apple_embedded.mm                            */
/**************************************************************************/
/*                         This file is part of:                          */
/*                             GODOT ENGINE                               */
/*                        https://godotengine.org                         */
/**************************************************************************/
/* Copyright (c) 2014-present Godot Engine contributors (see AUTHORS.md). */
/* Copyright (c) 2007-2014 Juan Linietsky, Ariel Manzur.                  */
/*                                                                        */
/* Permission is hereby granted, free of charge, to any person obtaining  */
/* a copy of this software and associated documentation files (the        */
/* "Software"), to deal in the Software without restriction, including    */
/* without limitation the rights to use, copy, modify, merge, publish,    */
/* distribute, sublicense, and/or sell copies of the Software, and to     */
/* permit persons to whom the Software is furnished to do so, subject to  */
/* the following conditions:                                              */
/*                                                                        */
/* The above copyright notice and this permission notice shall be         */
/* included in all copies or substantial portions of the Software.        */
/*                                                                        */
/* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,        */
/* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF     */
/* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. */
/* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY   */
/* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,   */
/* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE      */
/* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                 */
/**************************************************************************/

#include "rendering_native_surface_apple_embedded.h"

#include "core/object/class_db.h"
#include "core/object/ref_counted.h"
#include "core/string/ustring.h"
#include "core/variant/native_ptr.h"
#include "servers/rendering/rendering_context_driver.h"

#if defined(VULKAN_ENABLED)
#include "rendering_context_driver_vulkan_apple_embedded.h"
#endif

#ifdef METAL_ENABLED
#include "drivers/metal/rendering_context_driver_metal.h"
#include "servers/rendering/rendering_device.h"
#endif

void RenderingNativeSurfaceAppleEmbedded::_bind_methods() {
	ClassDB::bind_static_method("RenderingNativeSurfaceAppleEmbedded", D_METHOD("create", "layer"), &RenderingNativeSurfaceAppleEmbedded::create_api);
}

Ref<RenderingNativeSurfaceAppleEmbedded> RenderingNativeSurfaceAppleEmbedded::create_api(GDExtensionConstPtr<const void> p_layer) {
	return RenderingNativeSurfaceAppleEmbedded::create((__bridge CALayerPtr)p_layer.operator const void *());
}

Ref<RenderingNativeSurfaceAppleEmbedded> RenderingNativeSurfaceAppleEmbedded::create(CALayerPtr p_layer) {
	Ref<RenderingNativeSurfaceAppleEmbedded> result = memnew(RenderingNativeSurfaceAppleEmbedded);
	result->layer = p_layer;
	return result;
}

RenderingContextDriver *RenderingNativeSurfaceAppleEmbedded::create_rendering_context(const String &p_driver_name) {
#if defined(VULKAN_ENABLED)
	if (p_driver_name == "vulkan") {
		return memnew(RenderingContextDriverVulkanAppleEmbedded);
	}
#endif
#ifdef METAL_ENABLED
	if (p_driver_name == "metal") {
		if (@available(iOS 14.0, *)) {
			GODOT_CLANG_WARNING_PUSH_AND_IGNORE("-Wunguarded-availability")
			// Eliminate "RenderingContextDriverMetal is only available on iOS 14.0 or newer".
			return memnew(RenderingContextDriverMetal);
			GODOT_CLANG_WARNING_POP
		}
	}
#endif
	return nullptr;
}

RenderingNativeSurfaceAppleEmbedded::RenderingNativeSurfaceAppleEmbedded() {
	layer = nullptr;
}

RenderingNativeSurfaceAppleEmbedded::~RenderingNativeSurfaceAppleEmbedded() {
	// Does nothing.
}
