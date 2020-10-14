#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include <math.h>

#include "../../simulation_environment/Approssimazione-1/Motorcycle.h"

using namespace std;

#define numVAOs 1
//VAO = Vertex Array Objects

GLuint renderingProgram; //GLuint è una shortcat per unsigned int
GLuint vao[numVAOs];
GLuint xLoc, yLoc;

float XMotorcycle = 0.9, YMotorcycle = 0.9;

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
  glPointSize(5.0f); //Setta la grandezza di un Punto!
}

void display (GLFWwindow* window, double currentTime){
    glClear(GL_DEPTH_BUFFER_BIT);
    glClearColor(0.0, 0.0, 0.0, 1.0);
    glClear(GL_COLOR_BUFFER_BIT);
    glUseProgram(renderingProgram);
    
    xLoc = glGetUniformLocation(renderingProgram, "x");
    yLoc = glGetUniformLocation(renderingProgram, "y");
    glUniform1f(xLoc, (float)XMotorcycle);
    glUniform1f(yLoc, (float)YMotorcycle);
    glDrawArrays(GL_POINTS, 0, 1);
}

int main(void){
    if (!glfwInit()) {exit(EXIT_FAILURE);}
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    GLFWwindow* window = glfwCreateWindow(1000, 1000, "FirstVisualizer2D", NULL, NULL);
    glfwMakeContextCurrent(window);
    if (glewInit() != GLEW_OK){exit(EXIT_FAILURE);}
    glfwSwapInterval(1);

    init(window);
    //--------------------------------------
    Motorcycle m1(1, 1, 5, 10);
    double T = 0;
    double t = 0.01;
    m1.setAs(5);
    //--------------------------------------
    while (!glfwWindowShouldClose(window)) {
        display(window, glfwGetTime());
        glfwSwapBuffers(window);
        glfwPollEvents();
        //--------------------------------------
        XMotorcycle = m1.getX();
        YMotorcycle = m1.getY();
        T = T+t;
        m1.Integrate(t); 
        //--------------------------------------
    }
    glfwDestroyWindow(window);
    glfwTerminate();
    exit(EXIT_SUCCESS);
}
