#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <string>
#include <iostream>
#include <fstream>
#include <cmath>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include "Utils.h"
#include "CreateTrackFromDataFile.cpp"

using namespace std;

#define numVAOs 1
#define numVBOs 2
#define PASSOSCALE 0.1f
#define PASSOCAMERA 1.0f
#define PASSOVISUALE 0.1f
//VAO = Vertex Array Objects
//VBO = Vertex Buffer Objects

float scale = 1.0f;
float cameraX , cameraY, cameraZ;
float lookingDirX, lookingDirY, lookingDirZ;

float backmousex=0, backmousey=0;
bool mouseblocked = false;

float * vertices;
int NumOfVertices;
GLuint renderingProgram; //GLuint è una shortcat per unsigned int
GLuint vao[numVAOs];
GLuint vbo[numVBOs];

//Variabili allocate in init così non devono essere allocate durante il rendering
GLuint mvLoc, projLoc;
int width, height;
float aspect;
glm::mat4 pMat, vMat, mMat, mvMat;
/*
 * pMat : Perspective matrix
 * vMat : View matrix
 * mMat : Model matrix
 * mvMat : vMat*mMat
*/

void setupVertices(){
    /*float arr[18] = {
                -0.5, -0.5, 0,
                0.5, -0.5, 0,
                -0.5, 0.5, 0,

                -0.5, 0.5, 0,
                0.5, 0.5, 0,
                0.5, -0.5, 0
             };*/
    glGenVertexArrays(1, vao);
    glBindVertexArray(vao[0]);
    glGenBuffers(numVBOs, vbo);

    glBindBuffer(GL_ARRAY_BUFFER, vbo[0]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(float)*NumOfVertices, vertices, GL_STATIC_DRAW);
}

void init (GLFWwindow* window){
    renderingProgram = createShaderProgram((char *)"vertShader.glsl",(char *) "fragShader.glsl");
    cameraX = 0.0f; cameraY = 1.0f; cameraZ = 0.0f;
    lookingDirX = 0; lookingDirY = 0; lookingDirZ = -1;
    setupVertices();
}

void display (GLFWwindow* window, double currentTime){

    //lookingDirX = 10*cos((float)currentTime);
    glClear(GL_DEPTH_BUFFER_BIT);
    glClearColor(0.0, 0.0, 0.0, 1.0);
    glClear(GL_COLOR_BUFFER_BIT); //Clear the background to black
    glUseProgram(renderingProgram);

    //Getto le uniform
    mvLoc = glGetUniformLocation(renderingProgram, "mv_matrix");
    projLoc = glGetUniformLocation(renderingProgram, "proj_matrix");

    //Costruisco la pMat
    glfwGetFramebufferSize(window, &width, &height);
    aspect = (float)width / (float)height;
    pMat = glm::perspective(1.0472f, aspect, 0.1f, 1000.0f); //1.0472 radians = 60 degrees

    //Costruisco la mvMat
    vMat = glm::lookAt(glm::vec3(cameraX, cameraY, cameraZ), glm::vec3(cameraX+lookingDirX, cameraY+lookingDirY, cameraZ+lookingDirZ), glm::vec3(0.0f, 1.0f, 0.0f));
    mMat = glm::rotate(glm::mat4(1.0f), 0.785398f*2, glm::vec3(-1.0f, 0.0f, 0.0f));
    mMat = glm::translate(mMat, glm::vec3(-vertices[0]*scale, -vertices[1]*scale, 0));
    mMat = glm::scale(mMat, glm::vec3( scale, scale, scale));
    mvMat = vMat * mMat;

    //Spedisco matrici allo shader
    glUniformMatrix4fv(mvLoc, 1, GL_FALSE, glm::value_ptr(mvMat));
    glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(pMat));

    //Associazione VBO
    glBindBuffer(GL_ARRAY_BUFFER, vbo[0]);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
    glEnableVertexAttribArray(0);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);
    glDrawArrays(GL_TRIANGLES, 0, NumOfVertices);
}

void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods){
    cout<<"KEY:"<<key<<" - "<<glfwGetKeyScancode(key)<<endl;
    /*FrecciaSu : 265
     *FrecciaGiu : 264
     *FrecciaSx : 263
     *FrecciaDx : 262
    */
    if (glfwGetKey(window, 265) == GLFW_PRESS){
        //cameraZ-=PASSOCAMERA;
        //cameraZ+=(lookingZ-cameraZ)/(lookingX*lookingX+lookingY*lookingY+lookingZ*lookingZ);
        //cameraX+=(lookingX-cameraX)/(lookingX*lookingX+lookingY*lookingY+lookingZ*lookingZ);
        //cameraY+=(lookingY-cameraY)/(lookingX*lookingX+lookingY*lookingY+lookingZ*lookingZ);
    }
    if (glfwGetKey(window, 264) == GLFW_PRESS){
        //cameraZ+=PASSOCAMERA;
    }
    if (glfwGetKey(window, 263) == GLFW_PRESS){
        cameraX=cameraX-PASSOCAMERA;
    }
    if (glfwGetKey(window, 262) == GLFW_PRESS){
        cameraX=cameraX+PASSOCAMERA;
    }
    if (glfwGetKey(window, 334) == GLFW_PRESS ||
        glfwGetKey(window, 93) == GLFW_PRESS){
        scale+=PASSOSCALE;
    }
    if (glfwGetKey(window, 333) == GLFW_PRESS ||
        glfwGetKey(window, 47) == GLFW_PRESS){
        if (scale-PASSOSCALE!=0){
          scale-=PASSOSCALE;
        }
    }
    if (glfwGetKey(window, 256) == GLFW_PRESS){
        if (mouseblocked){
          glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_NORMAL);
          mouseblocked = false;
        }else{
          glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
          mouseblocked = true;
        }
    }
}

static void cursor_position_callback(GLFWwindow* window, double xpos, double ypos){
  //NON DEVO RUOTARE ATTORNO AD X MA ATTORNO AD UN ASSE CHE VARIA
  if (mouseblocked){
    float newlookingDirX = lookingDirX;
    float newlookingDirZ = lookingDirZ;
    float newlookingDirY = lookingDirY;
    float thetax = PASSOVISUALE*abs(backmousex-xpos)/50;
    float thetay = PASSOVISUALE*abs(backmousey-ypos)/200;
    if (xpos>backmousex){
      newlookingDirX = cos(thetax)*lookingDirX+
      sin(thetax)*lookingDirZ;
      newlookingDirZ = -sin(thetax)*lookingDirX+
      cos(thetax)*lookingDirZ;
    }
    if (xpos<backmousex){
      newlookingDirX = cos(-thetax)*lookingDirX+
      sin(-thetax)*lookingDirZ;
      newlookingDirZ = -sin(-thetax)*lookingDirX+
      cos(-thetax)*lookingDirZ;
    }
    if (ypos>backmousey && atan(lookingDirY/(sqrt(lookingDirX*lookingDirX+lookingDirZ*lookingDirZ)))>-0.785398f){
      newlookingDirY = cos(thetay)*lookingDirY-
      sin(thetay)*lookingDirZ;
      newlookingDirZ = sin(thetay)*lookingDirY+
      cos(thetay)*lookingDirZ;
    }
    if (ypos<backmousey){
      newlookingDirY = cos(-thetay)*lookingDirY-
      sin(-thetay)*lookingDirZ;
      newlookingDirZ = sin(-thetay)*lookingDirY+
      cos(-thetay)*lookingDirZ;
    }
    lookingDirX = newlookingDirX/sqrt(newlookingDirX*newlookingDirX+newlookingDirZ*newlookingDirZ+newlookingDirY*newlookingDirY);
    lookingDirZ = newlookingDirZ/sqrt(newlookingDirX*newlookingDirX+newlookingDirZ*newlookingDirZ+newlookingDirY*newlookingDirY);
    lookingDirY = newlookingDirY/sqrt(newlookingDirX*newlookingDirX+newlookingDirZ*newlookingDirZ+newlookingDirY*newlookingDirY);
    backmousex = xpos;
    backmousey = ypos;
    //cout << xpos << ";" << ypos << endl;
  }
}
void window_size_callback(GLFWwindow* window, int newWidth, int newHeight){
  aspect = (float)newWidth/(float)newHeight;
  glViewport(0, 0, newWidth, newHeight);
  pMat = glm::perspective(1.0472f, aspect, 0.1f, 1000.0f); //1.0472 radians = 60 degrees
}
int main(void){
    if (!glfwInit()) {exit(EXIT_FAILURE);}
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    GLFWwindow* window = glfwCreateWindow(1000, 1000, "09_TriangoloRotante", NULL, NULL);
    glfwMakeContextCurrent(window);
    if (glewInit() != GLEW_OK){exit(EXIT_FAILURE);}
    glfwSwapInterval(1);

    TrackData TD(TRACKFILENAME, 1);
    vertices = TD.getVerticesArray();
    NumOfVertices = TD.getNumOfVertices();
    init(window);
    glfwSetKeyCallback(window, key_callback);
    glfwSetCursorPosCallback(window, cursor_position_callback);
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
    mouseblocked=true;
    glfwSetWindowSizeCallback(window, window_size_callback);

    while (!glfwWindowShouldClose(window)) {
        display(window, glfwGetTime());
        glfwSwapBuffers(window);
        glfwPollEvents();
    }
    glfwDestroyWindow(window);
    glfwTerminate();
    exit(EXIT_SUCCESS);
}
