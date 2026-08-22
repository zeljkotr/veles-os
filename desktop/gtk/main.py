#!/usr/bin/env python3
"""
VELES OS Native Desktop - GTK4
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio

class VELESDesktop(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='os.veles.desktop')
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        # Glavni prozor
        window = Gtk.ApplicationWindow(application=app)
        window.set_title('VELES OS')
        window.set_default_size(1024, 768)
        
        # Glavni box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.set_child(main_box)
        
        # Header
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label='VELES OS'))
        window.set_titlebar(header)
        
        # Sidebar + Content
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(paned)
        
        # Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sidebar.set_size_request(200, -1)
        paned.set_start_child(sidebar)
        
        # Sidebar buttons
        pages = {
            'Dashboard': 'dashboard',
            'System': 'system',
            'Chat': 'chat',
            'Services': 'services',
            'Settings': 'settings'
        }
        
        for label, page_name in pages.items():
            btn = Gtk.Button(label=label)
            btn.set_halign(Gtk.Align.FILL)
            sidebar.append(btn)
        
        # Content area
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        paned.set_end_child(content)
        
        # Welcome label
        welcome = Gtk.Label(label='Welcome to VELES OS')
        content.append(welcome)
        
        window.present()

if __name__ == '__main__':
    app = VELESDesktop()
    app.run()
