#include <iostream>
#include <fstream>
using namespace std;

int main(){
    double STEP = 0.1;
    ofstream myfile;
    myfile.open ("../PositionData.dat");
    myfile << "X\tY\tphi\n";
    for (int i=0;i<100000;i++){
        myfile << STEP*i << "_1.00_0_\n";
    }
    myfile.close();
}
