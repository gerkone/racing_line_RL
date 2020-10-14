#include <iostream>
#include <fstream>
 using namespace std;
 
int main(){
    double STEP = 0.01;
    ofstream myfile;
    myfile.open ("../PositionData.dat");
    myfile << "X\tY\tphi\n";
    for (int i=0;i<1000;i++){
        myfile << STEP*i << "\t0\t0\n";
    }
    myfile.close();
}
