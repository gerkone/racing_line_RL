#include <iostream>
#include <math.h>
#include <vector>
#include <fstream>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
using namespace std;

#define TRACKFILENAME "trackdata_4387235659010134370.txt"
class TrackData{
private:
  vector<glm::vec3> points; //real data
  vector<float> vertices; //vertices with repetition for drawing
  vector<glm::vec3> normals; //normal versor
  float* vert;  //array for drawing

  glm::vec3 calcNormal(glm::vec3 firstPoint, glm::vec3 secondPoint){
    double x = firstPoint.y - secondPoint.y;
    double y = -firstPoint.x + secondPoint.x;
    double modules = sqrt(x*x+y*y);
    if (modules!=0){
      return glm::vec3(x/modules, y/modules, 0);
    }else{
      return glm::vec3(0, 0, 0);
    }
  }
  void addPointToVertices(glm::vec3 point){
    vertices.push_back(point.x);
    vertices.push_back(point.y);
    vertices.push_back(point.z);
  }
public:
  TrackData(string fileName, float width){
    ifstream fileStream(fileName, ios::in);
    string line;
    getline(fileStream, line);
    getline(fileStream, line);
    while (!fileStream.eof()){
        int posx = line.find("_");
        string x = line.substr(0, posx);
        string y = line.substr(posx+1);
        glm::vec3 point(stod(x), stod(y), 0);
        points.push_back(point);
        getline(fileStream, line);
    }
    /*for (int i=0; i<points.size()-1; i++){
      //Normal calculation
      normals.push_back(calcNormal(points[i], points[i+1]));
      //Vertex calculation
      vertices.push_back((points[i]+normals[i]*width).x);
      vertices.push_back((points[i]+normals[i]*width).y);
      vertices.push_back((points[i]+normals[i]*width).z);
      vertices.push_back((points[i]-normals[i]*width).x);
      vertices.push_back((points[i]-normals[i]*width).y);
      vertices.push_back((points[i]-normals[i]*width).z);
      vertices.push_back((points[i+1]+normals[i]*width).x);
      vertices.push_back((points[i+1]+normals[i]*width).y);
      vertices.push_back((points[i+1]+normals[i]*width).z);
      vertices.push_back((points[i+1]+normals[i]*width).x);
      vertices.push_back((points[i+1]+normals[i]*width).y);
      vertices.push_back((points[i+1]+normals[i]*width).z);
      vertices.push_back((points[i]-normals[i]*width).x);
      vertices.push_back((points[i]-normals[i]*width).y);
      vertices.push_back((points[i]-normals[i]*width).z);
      vertices.push_back((points[i+1]-normals[i]*width).x);
      vertices.push_back((points[i+1]-normals[i]*width).y);
      vertices.push_back((points[i+1]-normals[i]*width).z);
    }
    vertices.push_back((points[points.size()-1]+normals[0]*width).x);
    vertices.push_back((points[points.size()-1]+normals[0]*width).y);
    vertices.push_back((points[points.size()-1]+normals[0]*width).z);
    vertices.push_back((points[points.size()-1]-normals[0]*width).x);
    vertices.push_back((points[points.size()-1]-normals[0]*width).y);
    vertices.push_back((points[points.size()-1]-normals[0]*width).z);
    vertices.push_back((points[0]+normals[0]*width).x);
    vertices.push_back((points[0]+normals[0]*width).y);
    vertices.push_back((points[0]+normals[0]*width).z);
    vertices.push_back((points[0]+normals[0]*width).x);
    vertices.push_back((points[0]+normals[0]*width).y);
    vertices.push_back((points[0]+normals[0]*width).z);
    vertices.push_back((points[points.size()-1]-normals[0]*width).x);
    vertices.push_back((points[points.size()-1]-normals[0]*width).y);
    vertices.push_back((points[points.size()-1]-normals[0]*width).z);
    vertices.push_back((points[0]-normals[0]*width).x);
    vertices.push_back((points[0]-normals[0]*width).y);
    vertices.push_back((points[0]-normals[0]*width).z);*/
    normals.push_back(calcNormal(points[0], points[1]));
    for (int i=0; i<points.size()-2; i++){
        normals.push_back(calcNormal(points[i+1], points[i+2]));

        //first triangle
        addPointToVertices(points[i]-normals[i]*width);
        addPointToVertices(points[i]+normals[i]*width);
        addPointToVertices(points[i+1]+normals[i+1]*width);

        //second triangle
        addPointToVertices(points[i+1]+normals[i+1]*width);
        addPointToVertices(points[i+1]-normals[i+1]*width);
        addPointToVertices(points[i]-normals[i]*width);
    }
    normals.push_back(calcNormal(points[points.size()-2], points[points.size()-1]));
    //first triangle
    addPointToVertices(points[points.size()-2]-normals[points.size()-2]*width);
    addPointToVertices(points[points.size()-2]+normals[points.size()-2]*width);
    addPointToVertices(points[points.size()-1]+normals[points.size()-1]*width);

    //second triangle
    addPointToVertices(points[points.size()-1]+normals[points.size()-1]*width);
    addPointToVertices(points[points.size()-1]-normals[points.size()-1]*width);
    addPointToVertices(points[points.size()-2]-normals[points.size()-2]*width);

    //first triangle
    addPointToVertices(points[points.size()-1]-normals[points.size()-2]*width);
    addPointToVertices(points[points.size()-1]+normals[points.size()-2]*width);
    addPointToVertices(points[0]+normals[0]*width);

    //second triangle
    addPointToVertices(points[0]+normals[0]*width);
    addPointToVertices(points[0]-normals[0]*width);
    addPointToVertices(points[points.size()-1]-normals[points.size()-2]*width);
    /*cout << "(";
    for (int i=0; i<vertices.size(); i++){
      cout << vertices[i];
      if ((i+1)%3!=0){
        cout << ", ";
      }
      if ((i+1)%3==0 && i!=0){
        cout << ")";
      }
      if ((i+1)%18==0 && i!=0 && i!=vertices.size()-1){
        cout << "\n";
      }
      if ((i+1)%3==0 && i!=0 && i!=vertices.size()-1){
        cout << "(";
      }
    }*/
  }

  float * getVerticesArray(){
    vert = new float[vertices.size()];
    for (int i=0; i<vertices.size(); i++){
      vert[i] = vertices[i];
    }
    return vert;
  }
  int getNumOfVertices(){
    return vertices.size();
  }
};
