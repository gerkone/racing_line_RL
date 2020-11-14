#include <iostream>
#include <math.h>
using namespace std;

#include "Car.h"


int main(){
    Car m1(0.1, 0.3);
    double T = 0;
    double t = 0.01;
    setup();
    int storgi = 0;
    while(true){
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
    }
    /*for (int i=1; i<10; i++){
        cout << "s[ " << i << " ] = (" << m1.getX() << ", " << m1.getY() << ")" << endl;
        m1.Integrate(t);
        loop(m1.getX(), m1.getY());
    }
    m1.setMa(0);
    m1.setDelta(-0.5);
    for (int i=1; i<10; i++){
        cout << "s[ " << i << " ] = (" << m1.getX() << ", " << m1.getY() << ")" << endl;
        m1.Integrate(t);
        loop(m1.getX(), m1.getY());
    }
    while (true){}*/
}
