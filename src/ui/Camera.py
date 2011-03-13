__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.gl import *

import math
import euclid
from anim_euclid import AnimatedVector3, AnimatedQuaternion

fourfv = GLfloat*4
sixteenfv = GLfloat*16

class Camera(object):
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
    def __init__(self, pos):
        self._pos = AnimatedVector3(pos)
        self._orientation = AnimatedQuaternion()
        #self.viewangle = -7*math.pi/16
        #self.viewangle = -15*math.pi/32
        self.viewangle = -127*math.pi/256
        self._orientation.set(euclid.Quaternion().rotate_axis(self.viewangle, euclid.Vector3(1,0,0)))
        self._orientation.set_transition(dt=0.5, method="sine")
        self.view_switched = False
        self.vis_distance = 6.5
        self.x_limit = (-20, 20)
        self.y_limit = (15, 40)
        self.z_limit = (-20, 20)
    def setup(self):
        glPushMatrix()
        glLoadIdentity()
        glMultMatrixf(sixteenfv(*tuple(self.orientation.conjugated().get_matrix())))
        glTranslatef(*tuple(-1*self.pos))
    def reset(self):
        glPopMatrix()
    def move_by(self, delta):
        self._pos -= delta*0.1
        if self.pos.x < self.x_limit[0]: self._pos.x = self.x_limit[0]
        elif self.pos.x > self.x_limit[1]: self._pos.x = self.x_limit[1]
        if self.pos.y <= self.y_limit[0]: self._pos.y = self.y_limit[0]
        elif self.pos.y >= self.y_limit[1]: self._pos.y = self.y_limit[1]
        if self.pos.z < self.z_limit[0]: self._pos.z = self.z_limit[0]
        elif self.pos.z > self.z_limit[1]: self._pos.z = self.z_limit[1]
    def switch_viewpoint(self):
        axis = math.pi/2.+self.viewangle
        angle = math.pi
        if self.view_switched: angle = -1*math.pi
        self._orientation.rotate_axis(angle, euclid.Vector3(0,math.sin(axis),math.cos(axis)))
        self.view_switched = not self.view_switched
    def selection_ray(self, x, y):
        self.setup()
        model_view = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, model_view)
        projection = (GLdouble * 16)()
        glGetDoublev(GL_PROJECTION_MATRIX, projection)
        viewport = (GLint * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)

        x1, y1, z1 = GLdouble(), GLdouble(), GLdouble()
        x2, y2, z2 = GLdouble(), GLdouble(), GLdouble()
        gluUnProject(x, y, 0, model_view, projection, viewport, x1, y1, z1)
        gluUnProject(x, y, 1, model_view, projection, viewport, x2, y2, z2)
        ray = euclid.Ray3(euclid.Point3(x1.value, y1.value, z1.value),
                          euclid.Point3(x2.value, y2.value, z2.value))
        ray.v.normalize()
        self.reset()
        return ray
    def project_to_window(self, x,y,z):
        self.setup()
        model_view = (GLdouble * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, model_view)
        projection = (GLdouble * 16)()
        glGetDoublev(GL_PROJECTION_MATRIX, projection)
        viewport = (GLint * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)

        x1, y1, z1 = GLdouble(), GLdouble(), GLdouble()
        gluProject(x, y, z, model_view, projection, viewport, x1, y1, z1)
        self.reset()
        return euclid.Vector3(x1.value, y1.value, z1.value)
