#include <iostream>
#include <math.h>
using namespace std;

#include "Motorcycle.h"
#include "Grafica.cpp"


int main(){
    Motorcycle m1(0.1, 0);
    double T = 0;
    double t = 0.01;
    setup();
    int storgi = 0;
    while(true){
        /*cout << "s[" << T << "]=(" << m1.getX() << ", " << m1.getY() << ")";
        cout << endl;*/
        T = T+t;
        m1.Integrate(t); 
        storgi = loop(m1.getX(), m1.getY());
        if (storgi==-1){
            m1.storgiDx();
        }else if (storgi == 1){
            m1.storgiSx();
        }
        if (T>0.2){
            m1.setMa(0);
        }
        /*if ((int)(T) % 10 == 0){
            cout<<"("<<T<<")\n";
            m1.print();
        }*/
    }
}
