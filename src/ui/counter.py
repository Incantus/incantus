#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from math import sin, cos, tan, pi, atan2, sqrt, floor
from pyglet.gl import *

import anim
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion

INNER_DISC_RADIUS = .5

RING_RADIUS = 1.
RING_RADIUS_SEPARATION = 0.01
RING_HEIGHT = .5
RING_TEXTURE_RADIUS = INNER_DISC_RADIUS + \
                              3 * (RING_RADIUS + RING_RADIUS_SEPARATION) + \
                                                    RING_HEIGHT + .1
CONTROLLER_MARKER_RADIUS = 10
PIECE_SLICES = 40
PIECE_RADIUS = 20 #0.3
PIECE_HEIGHT = 0.1 #10 #0.1
PIECE_BEVEL = 0.03 #2 #0.03
sixteenfv = GLfloat*16

class Counter(anim.Animable):
    def pos(): 
        def fget(self): return euclid.Vector3(self._pos.x, self._pos.y, self._pos.z)
        def fset(self, val):
            self._pos.x = val.x
            self._pos.y = val.y
            self._pos.z = val.z
        return locals()
    pos = property(**pos())
    def orientation():
        def fget(self): return self._orientation.copy()
        def fset(self, val):
            self._orientation.x = val.x
            self._orientation.y = val.y
            self._orientation.z = val.z
            self._orientation.w = val.w
        return locals()
    orientation = property(**orientation())

    size = anim.Animatable()
    visible = anim.Animatable()
    alpha = anim.Animatable()

    piece_list = None
    radius = PIECE_RADIUS
    height = PIECE_HEIGHT

    def __init__(self, ctype, color=None):
        self.ctype = ctype
        if not color:
            color = [0, 0, 0]
            temp = hash(ctype) % 2**24
            color[0] = temp/2**16
            temp = temp % 2**16
            color[1] = temp/2**8
            color[2] = temp % 2**8
            self.color = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
        else: self.color = color
        self.size = anim.constant(1)
        self._pos = AnimatedVector3(0,0,0)
        self._orientation = AnimatedQuaternion()
        self.orientation = euclid.Quaternion.new_rotate_axis(pi, euclid.Vector3(0,0,1))
        self.visible = anim.constant(1.0)
        self.alpha = 0.9 #0.7 #anim.constant(1.0)
        cls = self.__class__
        if not cls.piece_list: self.build_piece_list(cls)

    def build_piece_list(self, cls):
        #def point_fn(i):
        #    return [(0, self.height),
        #            (cls.radius/2, cls.height),
        #            (cls.radius - PIECE_BEVEL, cls.height),
        #            (cls.radius, cls.height - PIECE_BEVEL),
        #            (cls.radius, PIECE_BEVEL),
        #            (cls.radius - PIECE_BEVEL, 0),
        #            ]
        cls.piece_list = glGenLists(1)
        glNewList(cls.piece_list, GL_COMPILE)
        # First version
        #glEnable(GL_BLEND)
        #glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        #glDisable(GL_BLEND)

        # Second version
        #glCullFace(GL_FRONT)
        #draw_lathe(point_fn, PIECE_SLICES)
        #glCullFace(GL_BACK)
        #draw_lathe(point_fn, PIECE_SLICES)

        # Third version
        draw_circle(0, 0, cls.radius)       # 2D circle function
        glEndList()

    def draw(self):
        if self.visible > 0:
            size = self.size
            glPushMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glMultMatrixf(sixteenfv(*tuple(self.orientation.get_matrix())))
            glScalef(size, size, size)
            glColor4f(self.color[0], self.color[1], self.color[2], self.alpha)
            glCallList(self.piece_list)
            glPopMatrix()

class ControllerMarker(Counter):
    """
    Subclass of counter to use for markers to indicate controller of permanents.
    """
    # This class needs its own piece_list and radius separate from Counter
    piece_list = None
    radius = CONTROLLER_MARKER_RADIUS

    alpha = anim.Animatable()

    def __init__(self, color):
        super(ControllerMarker, self).__init__('controller_marker', color=color)
        self.alpha = 0.4    # more transparent than regular counters

# Draw a rough circle approximation using 2D primatives
def draw_circle(cx, cy, r):
    num_segments = int(5 * sqrt(r))     # approximate the number of segments needed for a decent circle
    theta = 2 * pi / num_segments
    c = cos(theta)      # precalculate the sine and cosine
    s = sin(theta)
    x = r       # We start at angle = 0
    y = 0
    vertices = []

    for i in range(num_segments):
        vertices.extend((x + cx, y + cy))
        # Apply rotation to get the next vertex
        t = x;
        x = c * x - s * y;
        y = s * t + c * y;

    # Draw vertices using glDrawArrays since it's much faster
    num_coords = len(vertices)
    vertices = (GLfloat * num_coords)(*vertices)
    glPushAttrib(GL_ENABLE_BIT)
    glEnable(GL_NORMALIZE)
    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(2, GL_FLOAT, 0, vertices)
    glDrawArrays(GL_POLYGON, 0, num_coords/2)
    glPopClientAttrib()
    glPopAttrib()

# lathe around z to produce torus.  slice contains (rad, z) points
def draw_lathe(point_fn, slices, texr=RING_TEXTURE_RADIUS):
    vertices = []
    normals = []
    tex_coords = []

    a = 0
    incr = 2 * pi / slices
    lastslice = [(r, 0, z, r) for (r, z) in point_fn(slices)]
    for i in range(slices + 1):
        ca, sa = cos(a), sin(a)
        newslice = [(ca * r, sa * r, z, r) for (r, z) in point_fn(i)]
        lastp = None
        for ((x1, y1, z1, r1), (x2, y2, z2, r2)) in zip(lastslice, newslice):
            p = euclid.Point3(x1, y1, z1)
            if lastp:
                t1 = euclid.Vector3(x2 - x1, y2 - y1, z2 - z1)
                t2 = p - lastp
                n = t1.cross(t2)
                normal = (n.x, n.y, n.z)
            else:
                normal = (0, 0, -1)
            lastp = p
            r1 = (r1 + abs(z1)) / texr / 2
            r2 = (r2 + abs(z2)) / texr / 2
            normals.extend(normal)
            tex_coords.extend((ca * r2 + .5, sa * r2 + .5))
            vertices.extend((x2, y2, z2))
            normals.extend(normal)
            tex_coords.extend((ca * r1 + .5, sa * r1 + .5))
            vertices.extend((x1, y1, z1))
        lastslice = newslice
        a += incr

    vertices = (GLfloat * len(vertices))(*vertices)
    normals = (GLfloat * len(normals))(*normals)
    tex_coords = (GLfloat * len(tex_coords))(*tex_coords)
    count = 2 * len(lastslice)
    counts = [count for i in range(slices + 1)]
    counts = (GLint * len(counts))(*counts)
    firsts = range(0, (slices + 1) * count, count)
    firsts = (GLint * len(firsts))(*firsts)
    glPushAttrib(GL_ENABLE_BIT)
    glEnable(GL_NORMALIZE)
    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_NORMAL_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, vertices)
    glNormalPointer(GL_FLOAT, 0, normals)
    glTexCoordPointer(2, GL_FLOAT, 0, tex_coords)
    if gl_info.have_version(1, 4):
        glMultiDrawArrays(GL_QUAD_STRIP, firsts, counts, slices + 1)
    else:
        for first in firsts:
            glDrawArrays(GL_QUAD_STRIP, first, count)
    glPopClientAttrib()
    glPopAttrib()
