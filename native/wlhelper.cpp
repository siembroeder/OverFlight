#include <QtGui/qpa/qplatformwindow_p.h>
#include <QtGui/QWindow>
#include <wayland-client.h>
#include <cstdint>

extern "C" {

// Pass the raw QWindow* (as obtained from Python via shiboken6.getCppPointer).
// Returns the wl_surface* address, or 0 if unavailable (not yet created, or not Wayland).
uint64_t get_wayland_surface(uint64_t window_ptr) {
    auto *window = reinterpret_cast<QWindow *>(window_ptr);
    auto *waylandWindow = window->nativeInterface<QNativeInterface::Private::QWaylandWindow>();
    if (!waylandWindow) return 0;
    auto *surface = waylandWindow->surface();
    return reinterpret_cast<uint64_t>(surface);
}

// enabled=1 -> click-through (empty input region)
// enabled=0 -> restore normal input handling
void set_click_through(uint64_t display_ptr, uint64_t compositor_ptr,
                        uint64_t surface_ptr, int enabled) {
    auto *display    = reinterpret_cast<wl_display *>(display_ptr);
    auto *compositor = reinterpret_cast<wl_compositor *>(compositor_ptr);
    auto *surface    = reinterpret_cast<wl_surface *>(surface_ptr);
    if (!display || !compositor || !surface) return;

    if (enabled) {
        wl_region *region = wl_compositor_create_region(compositor);
        wl_surface_set_input_region(surface, region);
        wl_region_destroy(region);
    } else {
        wl_surface_set_input_region(surface, nullptr);
    }
    wl_surface_commit(surface);
    wl_display_flush(display);
}

} // extern "C"