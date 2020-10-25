#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <string>
#include <iostream>
#include <fstream>
#include <cmath>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include "./Utils.h"
#include <vector>
#include <stack>
#include "./BlenderImport/ImportedModel.cpp"

using namespace std;
#define numVAOs 2
#define numVBOs 3
#define INTERVALLOTEMPODATI 0.000001
#define PASSOCAMERA 0.1f
#define PASSOSTERZO 0.1f

float cameraX , cameraY, cameraZ;
float carLocX, carLocY;
int carposindex = 0;
GLuint renderingProgram; //GLuint è una shortcat per unsigned int
GLuint vao[numVAOs];
GLuint vbo0[numVBOs];
GLuint vbo1[numVBOs];

GLuint mvLoc, projLoc;
int width, height;
float aspect;
glm::mat4 pMat, vMat, mMat, mvMat;
stack<glm::mat4> mvStack;

//ANGOLI
float alpha = 0; //Angolo di moto delle ruote
float sterzo = 0; //Angolo ruote rispetto alla carrozzeria
float carphi = 0; //Angolo tra macchina e asse X

ImportedModel carrozzeria("./BlenderImport/Carrozzeria.obj");
ImportedModel ruotadx("./BlenderImport/Ruota.obj");

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

void setupVertices(void){
    glGenVertexArrays(numVAOs, vao);
    setupWheelVertices();
    setupCarrozzeriaVertices();
}

void init (GLFWwindow* window){
    renderingProgram = createShaderProgram((char *)"./BlenderImport/vertShader.glsl",(char *) "./BlenderImport/fragShader.glsl");
    cameraX = 0.0f; cameraY = 0.0f; cameraZ = 2.0f;
    setupVertices();
}

void display (GLFWwindow* window, double currentTime){
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
    vMat = glm::translate(glm::mat4(1.0f), glm::vec3(-cameraX, -cameraY, -cameraZ));
    mvStack.push(vMat);
    mvStack.top() *= glm::rotate(glm::mat4(1.0f), 1.57079633f/2, glm::vec3(1.0f, 0.0f, 0.0f));


    //Carrozzeria
    mvStack.push(mvStack.top());
    //mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(carLocX*0.01, 0, carLocY*0.01));
    mvStack.push(mvStack.top());
    mvStack.top() *= glm::rotate(glm::mat4(1.0f), carphi, glm::vec3(0.0f, 1.0f, 0.0f));
    mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( 0.005f, 0.005f, 0.005f ));

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
    mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(0.67*sin(carphi)-0.4*cos(carphi), 0.18, 0.67*cos(carphi)+0.4*sin(carphi)));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), alpha, glm::vec3(1, 0, 0));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), sterzo+carphi, glm::vec3(0, cos(alpha), -sin(alpha)));
    mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( 0.005f, 0.005f, 0.005f ));


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
    mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(0.67*sin(carphi)+0.4*cos(carphi), 0.18, 0.67*cos(carphi)-0.4*sin(carphi)));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), -alpha, glm::vec3(1, 0, 0));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), sterzo+carphi+3.14159f, glm::vec3(0, cos(-alpha), -sin(-alpha)));
    mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( 0.005f, 0.005f, 0.005f ));


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
    mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(-0.7*sin(carphi)-0.4*cos(carphi), 0.18, -0.7*cos(carphi)+0.4*sin(carphi)));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), alpha, glm::vec3(1, 0, 0));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), carphi, glm::vec3(0, cos(alpha), -sin(alpha)));
    mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( 0.005f, 0.005f, 0.005f ));


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
    mvStack.top() *= glm::translate(glm::mat4(1.0f), glm::vec3(-0.7*sin(carphi)+0.4*cos(carphi), 0.18, -0.7*cos(carphi)-0.4*sin(carphi)));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), -alpha, glm::vec3(1, 0, 0));
    mvStack.top() *=glm::rotate(glm::mat4(1.0f), carphi+3.14159f, glm::vec3(0, cos(-alpha), -sin(-alpha)));
    mvStack.top() *= glm::scale(glm::mat4(1.0f), glm::vec3( 0.005f, 0.005f, 0.005f ));


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
    if (glfwGetKey(window, 265) == GLFW_PRESS){
        cameraZ-=PASSOCAMERA;
    }
    if (glfwGetKey(window, 264) == GLFW_PRESS){
        cameraZ+=PASSOCAMERA;
    }
    if (glfwGetKey(window, 263) == GLFW_PRESS){
        cameraX-=PASSOCAMERA;
    }
    if (glfwGetKey(window, 262) == GLFW_PRESS){
        cameraX+=PASSOCAMERA;
    }
    if (glfwGetKey(window, 87) == GLFW_PRESS){//W
        cameraY+=PASSOCAMERA;
    }
    if (glfwGetKey(window, 83) == GLFW_PRESS){//S
        cameraY-=PASSOCAMERA;
    }
    if (glfwGetKey(window, 65) == GLFW_PRESS){//A
        sterzo+=PASSOSTERZO;
    }
    if (glfwGetKey(window, 68) == GLFW_PRESS){//A
        sterzo-=PASSOSTERZO;
    }
    if (glfwGetKey(window, 90) == GLFW_PRESS){//Z
        carphi+=PASSOSTERZO;
    }
    if (glfwGetKey(window, 88) == GLFW_PRESS){//X
        carphi-=PASSOSTERZO;
    }
    /*if (glfwGetKey(window, 334) == GLFW_PRESS ||
        glfwGetKey(window, 93) == GLFW_PRESS){
        scale+=PASSOSCALE;
    }
    if (glfwGetKey(window, 333) == GLFW_PRESS ||
        glfwGetKey(window, 47) == GLFW_PRESS){
        if (scale-PASSOSCALE!=0){
          scale-=PASSOSCALE;
        }
    }*/
}

int main(){
    //cout<<"Leggo File..."<<endl;
    ifstream fileStream("./PositionData.dat", ios::in);
    string line;
    getline(fileStream, line);
    getline(fileStream, line);
    vector<glm::vec3> carpos;
    while (!fileStream.eof()){
        int posx = line.find("_");
        string x = line.substr(0, posx);
        int posy = line.find("_", posx+1);
        string y = line.substr(posx+1,posy-posx-1);
        int posphi = line.find("_", posy+1);
        string phi = line.substr(posy+1, posphi-posy-1);
        //cout << line << endl;
        //cout << posx << "; " << posy << "; " << posphi << endl;
        //cout << x << ";" << y << ";" << phi << ";" << endl;
        carpos.push_back(glm::vec3( stod(x), stod(y), stod(phi)));
        getline(fileStream, line);
    }
    /*for (int i=0; i<carpos.size(); i++){
      cout << carpos[i].x << ";" << carpos[i].y << ";" << carpos[i].z << ";" << endl;
    }*/
    //cout<<"Lancio Programma..."<<endl;
    if (!glfwInit()) {exit(EXIT_FAILURE);}
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    GLFWwindow* window = glfwCreateWindow(1000, 1000, "FirstCar", NULL, NULL);
    glfwMakeContextCurrent(window);
    if (glewInit() != GLEW_OK){exit(EXIT_FAILURE);}
    glfwSwapInterval(1);

    init(window);
    glfwSetKeyCallback(window, key_callback);
    double oldTime = 0;
    double currentTime = 0;
    if (carpos.size()>0){
      carLocX = carpos[0].x;
      carLocY = carpos[0].y;
      carphi = carpos[0].z;
    }
    while (!glfwWindowShouldClose(window)) {
        oldTime = currentTime;
        currentTime = glfwGetTime();
        if (currentTime - oldTime > INTERVALLOTEMPODATI){
          //cout << currentTime << endl;
          if (carpos.size()>carposindex){
            carLocX = carpos[carposindex].x;
            carLocY = carpos[carposindex].y;
            //carphi = carpos[carposindex].z;
            carposindex++;
          }else{
            carposindex = 0;
          }
        }
        //carphi = cos(float(currentTime))+1.57079633f;
        alpha = float(currentTime);
        display(window, currentTime);
        glfwSwapBuffers(window);
        glfwPollEvents();
    }
    glfwDestroyWindow(window);
    glfwTerminate();
    exit(EXIT_SUCCESS);
}
