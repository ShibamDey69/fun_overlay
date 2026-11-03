#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, GdkPixbuf
import sys
import signal
from PIL import Image, ImageSequence
import cairo

class FloatingWidget(Gtk.Window):
    def __init__(self, gif_path):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        
        screen = self.get_screen()
        rgba = screen.get_rgba_visual()
        if rgba:
            self.set_visual(rgba)
        
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        GtkLayerShell.set_namespace(self, "floating-gif-widget")
        
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.BOTTOM, False)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, False)
        
        display = Gdk.Display.get_default()
        self.screen_width = 0
        self.screen_height = 0
        n_monitors = display.get_n_monitors()
        for i in range(n_monitors):
            monitor = display.get_monitor(i)
            geom = monitor.get_geometry()
            self.screen_width = max(self.screen_width, geom.x + geom.width)
            self.screen_height = max(self.screen_height, geom.y + geom.height)
        if self.screen_width == 0 or self.screen_height == 0:
            self.screen_width = 1920
            self.screen_height = 1080
        
        try:
            self.gif = Image.open(gif_path)
            self.frames = []
            for frame in ImageSequence.Iterator(self.gif):
                rgba = frame.convert("RGBA")
                data = rgba.tobytes()
                w, h = rgba.size
                pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                    GLib.Bytes.new(data),
                    GdkPixbuf.Colorspace.RGB,
                    True,
                    8,
                    w,
                    h,
                    w * 4
                )
                self.frames.append(pixbuf)
        except Exception:
            sys.exit(1)
        
        if not self.frames:
            sys.exit(1)

        self.scaled_frames = {}
            
        self.frame_index = 0
        self.scale = 0.7
        self.base_width = self.frames[0].get_width()
        self.base_height = self.frames[0].get_height()
        
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(
            int(self.base_width * self.scale),
            int(self.base_height * self.scale)
        )
        self.drawing_area.connect("draw", self.on_draw)
        
        box = Gtk.Box()
        box.pack_start(self.drawing_area, True, True, 0)
        self.add(box)
        
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.SCROLL_MASK
        )
        self.drawing_area.connect("button-press-event", self.on_press)
        self.drawing_area.connect("motion-notify-event", self.on_motion)
        self.drawing_area.connect("button-release-event", self.on_release)

        self.scroll_controller = Gtk.EventControllerScroll.new(
            self.drawing_area,
            Gtk.EventControllerScrollFlags.VERTICAL
        )
        self.scroll_controller.connect("scroll", self.on_scroll)

        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.window_x = 0
        self.window_y = 0
        
        w = int(self.base_width * self.scale)
        h = int(self.base_height * self.scale)
        self.window_x = self.screen_width - w - 40
        self.window_y = self.screen_height - h - 10
        
        self.update_position()
        self.update_frame()
        
        GLib.timeout_add(80, self.next_frame)
        self.show_all()
    
    def update_position(self):
        self.window_x = max(0, min(self.window_x, self.screen_width - 1))
        self.window_y = max(0, min(self.window_y, self.screen_height - 1))
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, int(self.window_x))
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, int(self.window_y))
    
    def on_press(self, widget, event):
        if event.button == 1:
            self.dragging = True
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            return True
        return False
    
    def on_motion(self, widget, event):
        if self.dragging:
            dx = event.x_root - self.drag_start_x
            dy = event.y_root - self.drag_start_y
            self.window_x += dx
            self.window_y += dy
            self.update_position()
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            return True
        return False
    
    def on_release(self, widget, event):
        if event.button == 1:
            self.dragging = False
            return True
        return False
    
    def on_scroll(self, _controller, _dx, dy):
        self.scale *= 1 - dy / 30.0
        self.scale = max(0.2, min(self.scale, 3.0))
        self.scaled_frames.clear()
        self.update_frame()
        return True
    
    def next_frame(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.update_frame()
        return True

    def on_draw(self, _widget, cr):
        Gdk.cairo_set_source_pixbuf(cr, self.scaled_frames[self.frame_index], 0, 0)
        cr.paint()
        return False

    def update_frame(self):
        w = int(self.base_width * self.scale)
        h = int(self.base_height * self.scale)

        cache_key = self.frame_index
        if cache_key not in self.scaled_frames:
            surface = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
            cr = cairo.Context(surface)
            cr.scale(self.scale, self.scale)
            Gdk.cairo_set_source_pixbuf(cr, self.frames[cache_key], 0, 0)
            cr.paint()
            self.scaled_frames[cache_key] = Gdk.pixbuf_get_from_surface(surface, 0, 0, w, h)
        scaled = self.scaled_frames[cache_key]

        self.drawing_area.set_size_request(scaled.get_width(), scaled.get_height())
        self.drawing_area.queue_draw()

def main():
    if len(sys.argv) != 2:
        sys.exit(1)
    
    app = FloatingWidget(sys.argv[1])
    
    def signal_handler(sig, frame):
        Gtk.main_quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()