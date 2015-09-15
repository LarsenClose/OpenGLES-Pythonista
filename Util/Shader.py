# coding: utf-8
from OpenGLES.GLES import gles2
from OpenGLES.GLES.gles2 import *
reload(gles2)

class ShaderSource(object):
    def __init__(self, source, shader_type):
        if isinstance(source, file):
            print "Source is of File type"
        self.source = source
        self.shader_type = shader_type
        self.compiled = False
        self.shader_id = None
        
    def compile(self):
        shader = glCreateShader(self.shader_type)
        if(shader == 0):
            print "Failed to create shader"
            return 0
        # Load the shader source
        char_arr = (ctypes.c_char_p * len(self.source))
        ca = char_arr()
        ca[0] = self.source
        args = (GLuint(shader),
                GLsizei(1),
                ca,
                GLint(0))
        glShaderSource(*args, argtypes_p=(GLuint, GLsizei, char_arr, GLint))
        # Compile the shader
        glCompileShader(shader)
        # Check the compile status
        compiled = GLint(0)
        sargs = (shader, GL_COMPILE_STATUS, ctypes.byref(compiled))
        glGetShaderiv(*sargs, argtypes_p=(GLuint, GLenum, ctypes.POINTER(GLint)))
        print "%s Shader Compile Status: %s" % ("Vertex" if self.shader_type == GL_VERTEX_SHADER else "Fragment", "success" if compiled.value == GL_TRUE else "fail")
        if(compiled.value == GL_FALSE):
            infoLen = GLint()
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, ctypes.byref(infoLen))
            if(infoLen > 1):
                print "Info len: ", infoLen.value
                infoLog = (ctypes.c_char_p * infoLen.value)()
                glGetShaderInfoLog(
                                    shader,
                                    infoLen.value,
                                    0,
                                    ctypes.byref(infoLog),
                                    argtypes_p=(GLuint,
                                                GLsizei,
                                                GLsizei,
                                                ctypes.POINTER((ctypes.c_char_p * infoLen.value))))
                print ctypes.string_at(infoLog)
            glDeleteShader(shader);
            return 0
        self.compiled = True
        self.shader_id = shader
        return shader
    

class ShaderProgram(object):
    def __init__(self, vertex_shader=None, fragment_shader=None, geometry_shader=None):
        self.compiled = False
        self.vertex, self.fragment, self.geometry = vertex_shader, fragment_shader, geometry_shader
        self.programObject = None
        self.uniforms = {}
        
    def build(self):
        if self.compiled:
            return
            
        if self.vertex:
            self.vertex.compile()
            if not self.vertex.compiled:
                raise RuntimeError("Could not compile vertex shader")
        if self.fragment:
            self.fragment.compile()
            if not self.fragment.compiled:
                raise RuntimeError("Could not compile fragment shader")
        if self.geometry:
            self.geometry.compile()
            if not self.geometry.compiled:
                raise RuntimeError("Could not compile geometry shader")
                
        programObject = glCreateProgram(None)
        if programObject > 0:
            if self.vertex:
                glAttachShader(programObject, self.vertex.shader_id);
            if self.fragment:
                glAttachShader(programObject, self.fragment.shader_id);
            if self.geometry:
                glAttachShader(programObject, self.geometry.shader_id);
            print "Shaders Compiled and Attatched"
            # Bind vPosition to attribute 0
            attr = (ctypes.c_char_p * 1024)()
            attr[0] = "vPosition"
            glBindAttribLocation(
                                    programObject,
                                    0,
                                    attr,
                                    argtypes_p=(GLuint,
                                                GLuint,
                                                ctypes.c_char_p * 1024));
            # Link the program
            glLinkProgram(programObject);
            # Check the link status
            print "Program Linked, Checking status"
            linked = GLint()
            glGetProgramiv(
                            programObject,
                            GL_LINK_STATUS,
                            ctypes.byref(linked),
                            argtypes_p=(GLuint,
                                        GLenum,
                                        ctypes.POINTER(GLint)))
            print "Linked Status in %s" % "success" if linked.value == GL_TRUE else "fail"
            if linked.value == GL_FALSE:
                infoLen = GLint()
                glGetProgramiv(programObject, GL_INFO_LOG_LENGTH, ctypes.byref(infoLen))
                if(infoLen > 1):
                    print "Info len: ", infoLen.value
                    infoLog = (ctypes.c_char_p * infoLen.value)()
                    glGetProgramInfoLog(
                                        programObject,
                                        infoLen,
                                        0,
                                        ctypes.byref(infoLog),
                                        argtypes_p=(GLuint,
                                                    GLsizei,
                                                    GLsizei,
                                                    ctypes.POINTER((ctypes.c_char_p * infoLen.value))))
                    print ctypes.string_at(infoLog)
                glDeleteProgram(programObject);
        self.programObject = programObject
        self.compiled = True
        
    def bind(self):
        if self.programObject:
            glUseProgram(self.programObject)
        else:
            raise ValueError("'ShaderProgram.programObject' is not set. Try running ShaderProgram.build() first")
            
    def unbind(self):
        glUseProgram(0)
        
    def uniformLocation(self, name):
        if name in self.uniforms:
            mid = self.uniforms[name]
        else:
            name_c_p = (GLchar * len(name))
            name_c = name_c_p()
            name_c[0] = name
            mid = glGetUniformLocation(
                                       self.programObject,
                                       name_c,
                                       argtypes_p=(GLuint,
                                                   name_c_p,
                                                   )
                                       )
                
            self.uniforms[name] = mid
            print name, mid
        return mid
        
    def uniform4x4(self, name, mat):
        mid = self.uniformLocation(name)
        if mid == -1:
            raise AttributeError("Could not find the location of the uniform: '%s'" % name)
        glUniformMatrix4fv(mid,
                           0,
                           GL_FALSE,
                           (GLfloat * 16)(*mat),
                           argtypes_p=(GLint,
                                       GLsizei,
                                       GLboolean,
                                       (GLfloat * 16)))