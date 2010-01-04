#!/usr/bin/env python
import pyglet
import shader

vec = '''
varying float xpos;
varying float ypos;
varying float zpos;

void main(void)
{
  xpos = clamp(gl_Vertex.x,0.0,1.0);
  ypos = clamp(gl_Vertex.y,0.0,1.0);
  zpos = clamp(gl_Vertex.z,0.0,1.0);

  gl_TexCoord[0] = gl_MultiTexCoord0;
  gl_Position = ftransform();

}'''

frag = '''
varying float xpos;
varying float ypos;
varying float zpos;

uniform sampler2D colorMap;
uniform float timer;

mat4 RGBToYCC =
mat4( 0.299,  0.587,  0.114,  0.000,
  0.701, -0.587, -0.114,  0.000,
 -0.299, -0.587,  0.886,  0.000,
  0.000,  0.000,  0.000,  1.000);

mat4 YCCToRGB =
mat4( 1.000,  1.000,  0.000,  0.000,
  1.000, -0.509, -0.194,  0.000,
  1.000,  0.000,  1.000,  0.000,
  0.000,  0.000,  0.000,  1.000);

void main (void)
{
    vec4 RGBA = vec4(xpos, ypos, zpos, 1.0)*0.25;
    vec4 YCCA = RGBToYCC * RGBA;
    float t;

    t = sin(timer*3.)*0.1;
    //YCCA.x += t;
    YCCA.y += t;
    YCCA.z += t;

    RGBA = YCCToRGB*YCCA;
    gl_FragColor = texture2D(colorMap, gl_TexCoord[0].st)+RGBA;//+clamp(RGBA, 0., 1.);
}
'''

class Foil(shader.ShaderProgram):
    def __init__(self):
        super(Foil, self).__init__()
        self.setShader(shader.VertexShader('foil_v', vec))
        self.setShader(shader.FragmentShader('foil_f', frag))
        self.timer = 0.
        pyglet.clock.schedule_interval(self.update, 1/60.0) # update at 60Hz
    def update(self, dt):
        self.timer += 0.05
        self.uset1F('timer', float(self.timer))
    def install(self):
        super(Foil, self).install()
        self.uset1F('timer', float(self.timer))

foil = Foil()
