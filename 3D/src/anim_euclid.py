
from anim import Animatable, Animable, add_time, animate, chain, constant
from euclid import Vector3, Quaternion, _EuclidMetaclass
from noconflict import classmaker

class AnimatedVector3(Animable, Vector3):
    __metaclass__ = classmaker()
    x = Animatable()
    y = Animatable()
    z = Animatable()
    def __init__(self, v, *args):
        if isinstance(v, Vector3): coor = tuple(v)
        else: coor = (v,)+args
        super(AnimatedVector3,self).__init__(*coor)
    def set(self, V):
        self.x = constant(V.x)
        self.y = constant(V.y)
        self.z = constant(V.z)
    def set_transition(self, dt, extend='constant', method='linear'):
        self.x = animate(self.x, self.x, dt=dt, extend=extend, method=method)
        self.y = animate(self.y, self.y, dt=dt, extend=extend, method=method)
        self.z = animate(self.z, self.z, dt=dt, extend=extend, method=method)
    def set_chained_transition(self, positions, dts, methods):
        assert len(positions) > 0
        if type(dts) == list or type(dts) == tuple:
            assert len(dts) == len(positions)
        else: dts = [dts]*len(positions)
        if type(methods) == list or type(methods) == tuple:
            assert len(methods) == len(positions)
        else: methods = [methods]*len(positions)
        x_chain = []; prev_x = self.x
        y_chain = []; prev_y = self.y
        z_chain = []; prev_z = self.z
        for pos, dt, method in zip(positions, dts, methods):
            x_chain.append(animate(prev_x, pos.x, dt=dt, method=method))
            y_chain.append(animate(prev_y, pos.y, dt=dt, method=method))
            z_chain.append(animate(prev_z, pos.z, dt=dt, method=method))
            prev_x = pos.x; prev_y = pos.y; prev_z = pos.z
        self.x = chain(x_chain)
        self.y = chain(y_chain)
        self.z = chain(z_chain)

class AnimatedQuaternion(Animable, Quaternion):
    __metaclass__ = classmaker()
    w = Animatable()
    x = Animatable()
    y = Animatable()
    z = Animatable()
    def set(self, Q):
        self.w = constant(Q.w)
        self.x = constant(Q.x)
        self.y = constant(Q.y)
        self.z = constant(Q.z)
    def set_transition(self, dt, extend="constant", method='linear'):
        self.w = animate(self.w, self.w, dt=dt, extend=extend, method=method)
        self.x = animate(self.x, self.x, dt=dt, extend=extend, method=method)
        self.y = animate(self.y, self.y, dt=dt, extend=extend, method=method)
        self.z = animate(self.z, self.z, dt=dt, extend=extend, method=method)
    def set_chained_transition(self, quaternions, dts, methods):
        assert len(quaternions) > 0
        if type(dts) == list or type(dts) == tuple:
            assert len(dts) == len(quaternions)
        else: dts = [dts]*len(quaternions)
        if type(methods) == list or type(methods) == tuple:
            assert len(methods) == len(quaternions)
        else: methods = [methods]*len(quaternions)
        w_chain = []; prev_w = self.w
        x_chain = []; prev_x = self.x
        y_chain = []; prev_y = self.y
        z_chain = []; prev_z = self.z
        for quat, dt, method in zip(quaternions, dts, methods):
            w_chain.append(animate(prev_w, quat.w, dt=dt, method=method))
            x_chain.append(animate(prev_x, quat.x, dt=dt, method=method))
            y_chain.append(animate(prev_y, quat.y, dt=dt, method=method))
            z_chain.append(animate(prev_z, quat.z, dt=dt, method=method))
            prev_w = quat.w; prev_x = quat.x; prev_y = quat.y; prev_z = quat.z
        self.w = chain(w_chain)
        self.x = chain(x_chain)
        self.y = chain(y_chain)
        self.z = chain(z_chain)

class BezierPath(object):
    def __init__(self, p0, p1, p2, p3):
        super(BezierPath,self).__init__()
        self.p0 = p0
        self.c = 3.0 * (p1 - p0)
        self.b = 3.0 * (p2 - p1) - self.c
        self.a = p3 - p0 - self.c - self.b
    def get(self, t):
        t_2 = t*t
        t_3 = t_2*t
        x = self.a*t_3 + self.b*t_2 + self.c*t + self.p0
        return x

if __name__ == "__main__":
    v = AnimatedVector3(1, 2, 3)
    v1 = Vector3(3, 4, 5)
    v2 = AnimatedVector3(v1)
    print v, v2
    v.set_transition(dt=5)
    v2.set_transition(dt=5)
    v += v1
    add_time(1)
    print v, v2
    v2 += Vector3(1,2,1)
    add_time(1)
    print v, v2
    add_time(4)
    print v, v2
