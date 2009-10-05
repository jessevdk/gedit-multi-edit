# -*- coding: utf-8 -*-
#
#  message.py - Multi Edit
#  
#  Copyright (C) 2009 - Jesse van den Kieboom
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#   
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#   
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

import glib
from signals import Signals
import gtk
import pango
import math

class Message(Signals):
    def __init__(self, view):
        Signals.__init__(self)

        self._view = view
        self._timeout_id = 0
        
        self._timeout_milli = 50
        self._fade_direction = 1
        self._fade_position = 0
        self._visible_counter = 0
        self._fade_speed = 0.2
        self._visible_max = 2000 / self._timeout_milli
        self._margin = (10, 5)
        
        self.connect_signal_after(self._view, 'expose-event', self.on_view_expose_event)
    
    def stop(self):
        self.hide()

        self.disconnect_signals(self._view)
        self._view = None
    
    def show(self, text):
        self._text = text
        self._fade_direction = 1
        self._visible_counter = 0
        
        if self._timeout_id == 0:
            self._timeout_id = glib.timeout_add(self._timeout_milli, self._animate_message)

    def hide(self):
        if self._timeout_id != 0:
            glib.source_remove(self._timeout_id)
            self._timeout_id = 0
            self._fade_position = 0
            
            self._view.queue_draw()

    def rounded_rectangle_path(self, ct, x, y, width, height, radius):
        ct.move_to(x + radius, y)

        ct.arc(x + width - radius, y + radius, radius, math.pi * 1.5, math.pi * 2)
        ct.arc(x + width - radius, y + height - radius, radius, 0, math.pi * 0.5)
        ct.arc(x + radius, y + height - radius, radius, math.pi * 0.5, math.pi)
        ct.arc(x + radius, y + radius, radius, math.pi, math.pi * 1.5)

    def darken(self, col, amount):
        for i in xrange(0, len(col)):
            col[i] = max(0, col[i] * (1 - amount))
    
    def from_color(self, col):
        return [col.red / float(0x10000), col.green / float(0x10000), col.blue / float(0x10000)]
    
    def on_view_expose_event(self, view, event):
        if self._timeout_id == 0 or event.window != view.get_window(gtk.TEXT_WINDOW_TEXT):
            return False

        # Render some message on top of it
        desc = pango.FontDescription('Sans 20')
        layout = view.create_pango_layout(self._text)
        layout.set_font_description(desc)
        
        extents = layout.get_pixel_extents()
        width = extents[1][2]
        height = extents[1][3]

        ctx = event.window.cairo_create()
        col = self.from_color(view.get_style().text[view.state])
        geom = event.window.get_geometry()
        
        x = (geom[2] - width) / 2
        y = (geom[3] - height) / 2

        ctx.set_line_width(1)
        ctx.translate(0.5, 0.5)
        
        bg = self.from_color(view.get_style().base[view.state])
        self.darken(bg, 0.1)
        
        ctx.save()
        
        rect = [x - self._margin[0], y - self._margin[1], width + 2 * self._margin[0], height + 2 * self._margin[1]]

        self.rounded_rectangle_path(ctx, rect[0], rect[1], rect[2], rect[3], 5)

        ctx.set_source_rgba(col[0], col[1], col[2], self._fade_position * 0.8)
        ctx.stroke_preserve()

        ctx.clip()
        ctx.set_source_rgba(bg[0], bg[1], bg[2], self._fade_position * 0.6)
        ctx.rectangle(rect[0], rect[1] + 0.5 * rect[3], rect[2], 0.5 * rect[3])
        ctx.fill()
        
        self.darken(bg, 0.1)
        ctx.set_source_rgba(bg[0], bg[1], bg[2], self._fade_position * 0.8)
        ctx.rectangle(rect[0], rect[1], rect[2], 0.5 * rect[3])
        ctx.fill()

        ctx.restore()
        ctx.set_source_rgba(col[0], col[1], col[2], self._fade_position)
        ctx.move_to(x, y)
        ctx.show_layout(layout)

        return False

    def _animate_message(self):
        self._fade_position += self._fade_direction * self._fade_speed
        ret = True

        if self._fade_position > 1:
            self._fade_position = 1
            self._visible_counter += 1
        elif self._fade_position < 0:
            self._visible_counter = 0
            self._timeout_id = 0
            ret = False
        
        if self._visible_counter > self._visible_max:
            self._fade_direction = -1
        
        self._view.queue_draw()
        return ret

# ex:ts=4:et:
