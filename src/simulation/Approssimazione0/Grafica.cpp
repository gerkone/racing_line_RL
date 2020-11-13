#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include <math.h>
using namespace std;

#define numVAOs 1
//VAO = Vertex Array Objects

GLuint renderingProgram; //GLuint è una shortcat per unsigned int
GLuint vao[numVAOs];
GLuint xLoc, yLoc;

bool storgiSx=false, storgiDx=false;

GLuint createShaderProgram() {
  const char *vshaderSource =
    "#version 430 \n"
    "uniform float x; \n"
    "uniform float y; \n"
    "void main(void) \n"
    "{gl_Position = vec4(x, y, 0.0, 1.0);}";
  const char *fshaderSource =
    "#version 430 \n"
    "out vec4 color; \n"
    "void main(void) \n"
    "{color = vec4(0.0, 0.0, 1.0, 1.0);}";
  GLuint vShader = glCreateShader(GL_VERTEX_SHADER);
  GLuint fShader = glCreateShader(GL_FRAGMENT_SHADER);

  glShaderSource(vShader, 1, &vshaderSource, NULL);
  glShaderSource(fShader, 1, &fshaderSource, NULL);

  glCompileShader(vShader);
  glCompileShader(fShader);

  GLuint vfProgram = glCreateProgram();
  glAttachShader(vfProgram, vShader);
  glAttachShader(vfProgram, fShader);
  glLinkProgram(vfProgram);

  return vfProgram;
}

void init (GLFWwindow* window){
  renderingProgram = createShaderProgram();
  glGenVertexArrays(numVAOs, vao);
  glBindVertexArray(vao[0]);
  glPointSize(1.0f); //Setta la grandezza di un Punto!
}

void display (GLFWwindow* window, double currentTime, double x, double y){
    /*glClear(GL_DEPTH_BUFFER_BIT);
    glClearColor(0.0, 0.0, 0.0, 1.0);
    glClear(GL_COLOR_BUFFER_BIT);*/
    glUseProgram(renderingProgram);
    
    xLoc = glGetUniformLocation(renderingProgram, "x");
    yLoc = glGetUniformLocation(renderingProgram, "y");
    glUniform1f(xLoc, (float)x);
    glUniform1f(yLoc, (float)y);
    glDrawArrays(GL_POINTS, 0, 1);
}

void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods){
    //cout<<"KEY:"<<key<<" - "<<glfwGetKeyScancode(key)<<endl;
    /*FrecciaSu : 265
     *FrecciaGiu : 264
     *FrecciaSx : 263
     *FrecciaDx : 262
    */
    if (key == 265 && action == GLFW_PRESS){
        
    }else if (key == 264 && action == GLFW_PRESS){
    }else if (key == 263 && action == GLFW_PRESS){
        storgiSx = true;
    }else if (key == 262 && action == GLFW_PRESS){
        storgiDx = true;
    }
}

GLFWwindow* window;
void setup(){    
    if (!glfwInit()) {exit(EXIT_FAILURE);}
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    window = glfwCreateWindow(1000, 1000, "Piano delle Fasi", NULL, NULL);
    glfwMakeContextCurrent(window);
    if (glewInit() != GLEW_OK){exit(EXIT_FAILURE);}
    glfwSwapInterval(1);
    
    init(window);
    glfwSetKeyCallback(window, key_callback);
    
}

int loop(double x, double y){
    storgiSx = false;
    storgiDx = false;
    if (!glfwWindowShouldClose(window)) {
        display(window, glfwGetTime(), x, y);
        glfwSwapBuffers(window);
        glfwPollEvents();
    }else{
        glfwDestroyWindow(window);
        glfwTerminate();
        exit(EXIT_SUCCESS);
    }
    if (glfwGetKey(window, 262) == GLFW_PRESS){
        return -1;
    }else if (glfwGetKey(window, 263) == GLFW_PRESS){
        return 1;
    }else{
        return 0;
    }
}
