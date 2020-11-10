#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <string>
#include <iostream>
#include <fstream>
#include <zmq.hpp>
#include <cmath>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <vector>
#include <stack>
#include "Utils.h"
#include "CreateTrackFromDataFile.cpp"
#include "BlenderImport/ImportedModel.cpp"
#include "Simulation/Car.h"

using namespace std;

#define numVAOs 3
#define numVBOs 3
#define PASSOSCALE 0.1f
#define PASSOCAMERA 1.0f
#define PASSOVISUALE 0.1f
#define DELTAT 0.1
//VAO = Vertex Array Objects
//VBO = Vertex Buffer Objects

float scale = 1.0f;
float scalecar = 0.001;
float cameraX , cameraY, cameraZ;
float lookingDirX, lookingDirY, lookingDirZ;
float carLocX, carLocY;
int carposindex = 0;
double xcorrection = 0;
double ycorrection = 0;

float backmousex=0, backmousey=0;
bool mouseblocked = false;

float * vertices;
int NumOfVerticesTrack;
GLuint renderingProgramTrack, renderingProgramCar; //GLuint è una shortcat per unsigned int
GLuint vao[numVAOs];
GLuint vbo[numVBOs];
GLuint vbo0[numVBOs];
GLuint vbo1[numVBOs];
GLuint vbo3[numVBOs];

//Variabili allocate in init così non devono essere allocate durante il rendering
GLuint mvLoc, projLoc;
int width, height;
float aspect;
glm::mat4 pMat, vMat, mMat, mvMat;
stack<glm::mat4> mvStack;
/*
 * pMat : Perspective matrix
 * vMat : View matrix
 * mMat : Model matrix
 * mvMat : vMat*mMat
*/

//ANGOLI
float alpha = 0; //Angolo di moto delle ruote
float sterzo = 0; //Angolo ruote rispetto alla carrozzeria
float carphi = 0; //Angolo tra macchina e asse X


ImportedModel carrozzeria("./BlenderImport/Carrozzeria.obj");
ImportedModel ruotadx("./BlenderImport/Ruota.obj");

//SIMULAZIONE
Car car(0, 0);

//Funzioni
glm::vec3 rotate(float, float, float, glm::vec3, float);
void displayTrack(GLFWwindow*, double);
void displayCar(GLFWwindow*, double);

void setupCarrozzeriaVertices(void){
    std::vector<glm::vec3> vert = carrozzeria.getVertices();
    std::vector<glm::vec2> tex = carrozzeria.getTextCoords();
    std::vector<glm::vec3> norm = carrozzeria.getNormalVecs();
    int numObjVertices = carrozzeria.getNumVertices();

    std::vector<float> pvalues; //vertex positions
    std::vector<float> tvalues; //texture coordinates
    std::vector<float> nvalues; //normal vectors

    for (int i=0; i<numObjVertices; i++){
        pvalues.push_back((vert[i]).x);
        pvalues.push_back((vert[i]).y);
        pvalues.push_back((vert[i]).z);
        tvalues.push_back((tex[i]).s);
        tvalues.push_back((tex[i]).t);
        nvalues.push_back((norm[i]).x);
        nvalues.push_back((norm[i]).y);
        nvalues.push_back((norm[i]).z);
    }
    glBindVertexArray(vao[0]);
    glGenBuffers(numVBOs, vbo0);

    //VBO for vertex location
    glBindBuffer(GL_ARRAY_BUFFER, vbo0[0]);
    glBufferData(GL_ARRAY_BUFFER, pvalues.size()*4, &pvalues[0], GL_STATIC_DRAW);

    //VBO for texture coordinates
    glBindBuffer(GL_ARRAY_BUFFER, vbo0[1]);
    glBufferData(GL_ARRAY_BUFFER, tvalues.size()*4, &tvalues[0], GL_STATIC_DRAW);

    //VBO for normal vectors
    glBindBuffer(GL_ARRAY_BUFFER, vbo0[2]);
    glBufferData(GL_ARRAY_BUFFER, nvalues.size()*4, &nvalues[0], GL_STATIC_DRAW);

}

void setupWheelVertices(void){
    std::vector<glm::vec3> vert = ruotadx.getVertices();
    std::vector<glm::vec2> tex = ruotadx.getTextCoords();
    std::vector<glm::vec3> norm = ruotadx.getNormalVecs();
    int numObjVertices = ruotadx.getNumVertices();

    std::vector<float> pvalues; //vertex positions
    std::vector<float> tvalues; //texture coordinates
    std::vector<float> nvalues; //normal vectors

    for (int i=0; i<numObjVertices; i++){
        pvalues.push_back((vert[i]).x);
        pvalues.push_back((vert[i]).y);
        pvalues.push_back((vert[i]).z);
        tvalues.push_back((tex[i]).s);
        tvalues.push_back((tex[i]).t);
        nvalues.push_back((norm[i]).x);
        nvalues.push_back((norm[i]).y);
        nvalues.push_back((norm[i]).z);
    }
    glBindVertexArray(vao[1]);
    glGenBuffers(numVBOs, vbo1);

    //VBO for vertex location
    glBindBuffer(GL_ARRAY_BUFFER, vbo1[0]);
    glBufferData(GL_ARRAY_BUFFER, pvalues.size()*4, &pvalues[0], GL_STATIC_DRAW);

    //VBO for texture coordinates
    glBindBuffer(GL_ARRAY_BUFFER, vbo1[1]);
    glBufferData(GL_ARRAY_BUFFER, tvalues.size()*4, &tvalues[0], GL_STATIC_DRAW);

    //VBO for normal vectors
    glBindBuffer(GL_ARRAY_BUFFER, vbo1[2]);
    glBufferData(GL_ARRAY_BUFFER, nvalues.size()*4, &nvalues[0], GL_STATIC_DRAW);

    glBindVertexArray(0);
}
void setupTrackVertices(void){
    glBindVertexArray(vao[2]);
    glGenBuffers(numVBOs, vbo3);

    glBindBuffer(GL_ARRAY_BUFFER, vbo3[0]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(float)*NumOfVerticesTrack, vertices, GL_STATIC_DRAW);
}

void setupVertices(){
    glGenVertexArrays(numVAOs, vao);
    setupTrackVertices();
    setupWheelVertices();
    setupCarrozzeriaVertices();
}

void init (GLFWwindow* window){
    renderingProgramTrack = createShaderProgram((char *)"Shader/vertShaderT.glsl",(char *) "Shader/fragShaderT.glsl");
    renderingProgramCar= createShaderProgram((char *)"Shader/vertShaderC.glsl",(char *) "Shader/fragShaderC.glsl");
    cameraX = 0.0f; cameraY = 2.0f; cameraZ = 0.0f;
    lookingDirX = -1; lookingDirY = 0; lookingDirZ = 0;
    setupVertices();
}

void display (GLFWwindow* window, double currentTime){

    //lookingDirX = 10*cos((float)currentTime);
    glClear(GL_DEPTH_BUFFER_BIT);
    glClearColor(0.0, 0.0, 0.0, 1.0);
    glClear(GL_COLOR_BUFFER_BIT); //Clear the background to black
    displayTrack(window, currentTime);
    displayCar(window, currentTime);
}

void displayTrack(GLFWwindow* window, double currentTime){
  glUseProgram(renderingProgramTrack);

  //Getto le uniform
  mvLoc = glGetUniformLocation(renderingProgramTrack, "mv_matrix");
  projLoc = glGetUniformLocation(renderingProgramTrack, "proj_matrix");

  //Costruisco la pMat
  glfwGetFramebufferSize(window, &width, &height);
  aspect = (float)width / (float)height;
  pMat = glm::perspective(1.0472f, aspect, 0.1f, 1000.0f); //1.0472 radians = 60 degrees

  //Costruisco la mvMat
  vMat = glm::lookAt(glm::vec3(cameraX, cameraY, cameraZ), glm::vec3(cameraX+lookingDirX, cameraY+lookingDirY, cameraZ+lookingDirZ), glm::vec3(0.0f, 1.0f, 0.0f));
  mMat = glm::rotate(glm::mat4(1.0f), (float)(0*M_PI/2), glm::vec3(0.0f, 1.0f, 0.0f));
  mMat = glm::rotate(mMat, (float)(M_PI/2), glm::vec3(1.0f, 0.0f, 0.0f));
  mMat = glm::translate(mMat, glm::vec3(-xcorrection*scale, -ycorrection*scale, 0));
  mMat = glm::scale(mMat, glm::vec3(scale, scale, scale));
  mvMat = vMat * mMat;

  //Spedisco matrici allo shader
  glUniformMatrix4fv(mvLoc, 1, GL_FALSE, glm::value_ptr(mvMat));
  glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(pMat));

  //Associazione VBO
  glBindBuffer(GL_ARRAY_BUFFER, vbo3[0]);
  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
  glEnableVertexAttribArray(0);
  glEnable(GL_DEPTH_TEST);
  glDepthFunc(GL_LEQUAL);
  glDrawArrays(GL_TRIANGLES, 0, NumOfVerticesTrack);
}

void displayCar(GLFWwindow* window, double currentTime){
  glUseProgram(renderingProgramCar);

  //Getto le uniform
  mvLoc = glGetUniformLocation(renderingProgramCar, "mv_matrix");
  projLoc = glGetUniformLocation(renderingProgramCar, "proj_matrix");

  //Costruisco la pMat
  glfwGetFramebufferSize(window, &width, &height);
  aspect = (float)width / (float)height;
  pMat = glm::perspective(1.0472f, aspect, 0.1f, 1000.0f); //1.0472 radians = 60 degrees

  //Costruisco la mvMat
  vMat = glm::lookAt(glm::vec3(cameraX, cameraY, cameraZ), glm::vec3(cameraX+lookingDirX, cameraY+lookingDirY, cameraZ+lookingDirZ), glm::vec3(0.0f, 1.0f, 0.0f));
  mvStack.push(vMat);


  //Carrozzeria
  mvStack.push(mvStack.top());
  mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(carLocX, 0.2, carLocY));
  mvStack.push(mvStack.top());
  mvStack.top() *= glm::rotate(glm::mat4(1.0f), carphi, glm::vec3(0.0f, 1.0f, 0.0f));
  mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( scalecar, scalecar, scalecar ));

  //Spedisco matrici allo shader
  glUniformMatrix4fv(mvLoc, 1, GL_FALSE, glm::value_ptr(mvStack.top()));
  glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(pMat));

  //Associazione VBO
  glBindVertexArray(vao[0]);
  glBindBuffer(GL_ARRAY_BUFFER, vbo0[0]);
  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
  glEnableVertexAttribArray(0);
  glEnable(GL_DEPTH_TEST);
  glDepthFunc(GL_LEQUAL);
  glDrawArrays(GL_TRIANGLES, 0, carrozzeria.getNumVertices());
  mvStack.pop();

  //Ruota Davanti DX
  mvStack.push(mvStack.top());
  mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(0.67*scalecar*200*sin(carphi)-0.4*scalecar*200*cos(carphi), 0.18*scalecar*200, 0.67*scalecar*200*cos(carphi)+0.4*scalecar*200*sin(carphi)));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), alpha, glm::vec3(1, 0, 0));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), sterzo+carphi, glm::vec3(0, cos(alpha), -sin(alpha)));
  mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( scalecar, scalecar, scalecar ));


  //Spedisco matrici allo shader
  glUniformMatrix4fv(mvLoc, 1, GL_FALSE, glm::value_ptr(mvStack.top()));
  glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(pMat));

  //Associazione VBO
  glBindVertexArray(vao[1]);
  glBindBuffer(GL_ARRAY_BUFFER, vbo1[0]);
  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
  glEnableVertexAttribArray(0);
  glEnable(GL_DEPTH_TEST);
  glDepthFunc(GL_LEQUAL);
  glDrawArrays(GL_TRIANGLES, 0, ruotadx.getNumVertices());
  mvStack.pop();

  //Ruota Davanti SX
  mvStack.push(mvStack.top());
  mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(0.67*scalecar*200*sin(carphi)+0.4*scalecar*200*cos(carphi), 0.18*scalecar*200, 0.67*scalecar*200*cos(carphi)-0.4*scalecar*200*sin(carphi)));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), -alpha, glm::vec3(1, 0, 0));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), sterzo+carphi+3.14159f, glm::vec3(0, cos(-alpha), -sin(-alpha)));
  mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( scalecar, scalecar, scalecar ));


  //Spedisco matrici allo shader
  glUniformMatrix4fv(mvLoc, 1, GL_FALSE, glm::value_ptr(mvStack.top()));
  glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(pMat));

  //Associazione VBO
  glBindVertexArray(vao[1]);
  glBindBuffer(GL_ARRAY_BUFFER, vbo1[0]);
  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
  glEnableVertexAttribArray(0);
  glEnable(GL_DEPTH_TEST);
  glDepthFunc(GL_LEQUAL);
  glDrawArrays(GL_TRIANGLES, 0, ruotadx.getNumVertices());
  mvStack.pop();

  //Ruota Dietro DX
  mvStack.push(mvStack.top());
  mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(-0.7*scalecar*200*sin(carphi)-0.4*scalecar*200*cos(carphi), 0.18*scalecar*200, -0.7*scalecar*200*cos(carphi)+0.4*scalecar*200*sin(carphi)));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), alpha, glm::vec3(1, 0, 0));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), carphi, glm::vec3(0, cos(alpha), -sin(alpha)));
  mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( scalecar, scalecar, scalecar ));


  //Spedisco matrici allo shader
  glUniformMatrix4fv(mvLoc, 1, GL_FALSE, glm::value_ptr(mvStack.top()));
  glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(pMat));

  //Associazione VBO
  glBindVertexArray(vao[1]);
  glBindBuffer(GL_ARRAY_BUFFER, vbo1[0]);
  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
  glEnableVertexAttribArray(0);
  glEnable(GL_DEPTH_TEST);
  glDepthFunc(GL_LEQUAL);
  glDrawArrays(GL_TRIANGLES, 0, ruotadx.getNumVertices());
  mvStack.pop();

  //Ruota Dietro SX
  mvStack.push(mvStack.top());
  mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(-0.7*scalecar*200*sin(carphi)+0.4*scalecar*200*cos(carphi), 0.18*scalecar*200, -0.7*scalecar*200*cos(carphi)-0.4*scalecar*200*sin(carphi)));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), -alpha, glm::vec3(1, 0, 0));
  mvStack.top() *=glm::rotate(glm::mat4(1.0f), carphi+3.14159f, glm::vec3(0, cos(-alpha), -sin(-alpha)));
  mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( scalecar, scalecar, scalecar ));


  //Spedisco matrici allo shader
  glUniformMatrix4fv(mvLoc, 1, GL_FALSE, glm::value_ptr(mvStack.top()));
  glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(pMat));

  //Associazione VBO
  glBindVertexArray(vao[1]);
  glBindBuffer(GL_ARRAY_BUFFER, vbo1[0]);
  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
  glEnableVertexAttribArray(0);
  glEnable(GL_DEPTH_TEST);
  glDepthFunc(GL_LEQUAL);
  glDrawArrays(GL_TRIANGLES, 0, ruotadx.getNumVertices());
  mvStack.pop();

  mvStack.pop();
  mvStack.pop();
}
void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods){
    //cout<<"KEY:"<<key<<" - "<<glfwGetKeyScancode(key)<<endl;
    /*FrecciaSu : 265
     *FrecciaGiu : 264
     *FrecciaSx : 263
     *FrecciaDx : 262
    */
    if (glfwGetKey(window, 265) == GLFW_PRESS){//freccia su
    }
    if (glfwGetKey(window, 264) == GLFW_PRESS){//freccia giu
    }
    if (glfwGetKey(window, 263) == GLFW_PRESS){//freccia sinistra
    }
    if (glfwGetKey(window, 262) == GLFW_PRESS){//freccia destra
    }
    if (glfwGetKey(window, 87) == GLFW_PRESS){//W
        cameraX += lookingDirX*PASSOCAMERA;
        //cameraY += lookingDirY*PASSOCAMERA;
        cameraZ += lookingDirZ*PASSOCAMERA;
    }
    if (glfwGetKey(window, 83) == GLFW_PRESS){//S
        cameraX -= lookingDirX*PASSOCAMERA;
        //cameraY += lookingDirY*PASSOCAMERA;
        cameraZ -= lookingDirZ*PASSOCAMERA;
    }
    if (glfwGetKey(window, 65) == GLFW_PRESS){//A
        car.storgiSx();
    }
    if (glfwGetKey(window, 68) == GLFW_PRESS){//D
        car.storgiDx();
    }
    if (glfwGetKey(window, 81) == GLFW_PRESS){//Q
        car.accelate();
    }
    if (glfwGetKey(window, 69) == GLFW_PRESS){//E
        car.stroke();
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
    glm::vec3 newlookingDir(lookingDirX, lookingDirY, lookingDirZ);
    float newlookingDirX = lookingDirX;
    float newlookingDirZ = lookingDirZ;
    float newlookingDirY = lookingDirY;
    float thetax = PASSOVISUALE*abs(backmousex-xpos)/50;
    float thetay = PASSOVISUALE*abs(backmousey-ypos)/200;
    if (xpos>backmousex){
      newlookingDir = rotate(0, 1, 0, glm::vec3(lookingDirX, lookingDirY, lookingDirZ), thetax);
      //cout << newlookingDirX;
      /*newlookingDirX = cos(thetax)*lookingDirX+
      sin(thetax)*lookingDirZ;
      cout << "; " << newlookingDirX << endl;
      newlookingDirZ = -sin(thetax)*lookingDirX+
      cos(thetax)*lookingDirZ;*/
    }
    if (xpos<backmousex){
      newlookingDir = rotate(0, 1, 0, glm::vec3(lookingDirX, lookingDirY, lookingDirZ), -thetax);
      /*newlookingDirX = cos(-thetax)*lookingDirX+
      sin(-thetax)*lookingDirZ;
      newlookingDirZ = -sin(-thetax)*lookingDirX+
      cos(-thetax)*lookingDirZ;*/
    }
    if (ypos>backmousey && atan(lookingDirY/(sqrt(lookingDirX*lookingDirX+lookingDirZ*lookingDirZ)))>-0.785398f){
      newlookingDir = rotate(-(lookingDirZ)/sqrt(lookingDirX*lookingDirX+lookingDirZ*lookingDirZ), 0, (lookingDirX)/sqrt(lookingDirX*lookingDirX+lookingDirZ*lookingDirZ), glm::vec3(lookingDirX, lookingDirY, lookingDirZ), thetay);
      /*newlookingDirY = cos(thetay)*lookingDirY-
      sin(thetay)*lookingDirZ;
      newlookingDirZ = sin(thetay)*lookingDirY+
      cos(thetay)*lookingDirZ;*/
    }
    if (ypos<backmousey && atan(lookingDirY/(sqrt(lookingDirX*lookingDirX+lookingDirZ*lookingDirZ)))<0.785398f){
      newlookingDir = rotate(-(lookingDirZ)/sqrt(lookingDirX*lookingDirX+lookingDirZ*lookingDirZ), 0, (lookingDirX)/sqrt(lookingDirX*lookingDirX+lookingDirZ*lookingDirZ), glm::vec3(lookingDirX, lookingDirY, lookingDirZ), -thetay);
      /*newlookingDirY = cos(-thetay)*lookingDirY-
      sin(-thetay)*lookingDirZ;
      newlookingDirZ = sin(-thetay)*lookingDirY+
      cos(-thetay)*lookingDirZ;*/
    }
    /*lookingDirX = newlookingDirX/sqrt(newlookingDirX*newlookingDirX+newlookingDirZ*newlookingDirZ+newlookingDirY*newlookingDirY);
    lookingDirZ = newlookingDirZ/sqrt(newlookingDirX*newlookingDirX+newlookingDirZ*newlookingDirZ+newlookingDirY*newlookingDirY);
    lookingDirY = newlookingDirY/sqrt(newlookingDirX*newlookingDirX+newlookingDirZ*newlookingDirZ+newlookingDirY*newlookingDirY);*/
    lookingDirX = newlookingDir.x;
    lookingDirY = newlookingDir.y;
    lookingDirZ = newlookingDir.z;
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
    GLFWwindow* window = glfwCreateWindow(1000, 1000, "Racing Line RL", NULL, NULL);
    glfwMakeContextCurrent(window);
    if (glewInit() != GLEW_OK){exit(EXIT_FAILURE);}
    glfwSwapInterval(1);

    TrackData TD(TRACKFILENAME, 1);
    vertices = TD.getVerticesArray();
    NumOfVerticesTrack = TD.getNumOfVertices();
    xcorrection = (vertices[0] + vertices[3])/2;
    ycorrection = (vertices[1] + vertices[4])/2;


    init(window);
    glfwSetKeyCallback(window, key_callback);
    glfwSetCursorPosCallback(window, cursor_position_callback);
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
    mouseblocked=true;
    glfwSetWindowSizeCallback(window, window_size_callback);

    // initialize the zmq context with a single IO thread
    zmq::context_t context{1};
    // construct a REQ (request) socket and connect to interface
    zmq::socket_t socket{context, zmq::socket_type::req};
    socket.connect("tcp://localhost:55555");

    const string ack{"ACK"};
    zmq::message_t reply{};

    // visualizer ready
    socket.send(zmq::buffer(ack), zmq::send_flags::none);

    while (!glfwWindowShouldClose(window)) {
        display(window, glfwGetTime());
        glfwSwapBuffers(window);
        glfwPollEvents();
        //SIMULAZIONE
        socket.recv(reply, zmq::recv_flags::none);
        string data = reply.to_string();

        // deserialize data string
        // formatted as {x}/{y}/{car_angle}/{front_tyres_angle}
        size_t pos = 0;
        vector<double> values;
        string token;
        while ((pos = data.find("/")) != string::npos) {
          token = data.substr(0, pos);
          values.push_back(stod(token));
          data.erase(0, pos + 1);
        }
        values.push_back(stod(data));

        // update environment variables
        carLocX = values.at(0)-xcorrection;
        carLocY = values.at(1)-ycorrection;
        carphi = M_PI/2 - values.at(2);
        sterzo = values.at(3);
        //cout << carLocX << ", " << carLocY << ", " << carphi << ", " << sterzo << endl;
        // send confirmation
        socket.send(zmq::buffer(ack), zmq::send_flags::none);

    }
    glfwDestroyWindow(window);
    glfwTerminate();
    exit(EXIT_SUCCESS);
}

glm::vec3 rotate(float x, float y, float z, glm::vec3 vec, float T){
  return glm::mat3( x*x+(1-x*x)*cos(T),       x*y*(1-cos(T))-z*sin(T),   x*z*(1-cos(T))+y*sin(T),
                    x*y*(1-cos(T))+z*sin(T),  y*y+(1-y*y)*cos(T),       y*z*(1-cos(T))-x*sin(T),
                    x*z*(1-cos(T))-y*sin(T),  y*z*(1-cos(T))+x*sin(T),  z*z+(1-z*z)*cos(T)
                  )*vec;
}
