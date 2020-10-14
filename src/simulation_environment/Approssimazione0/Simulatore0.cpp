#include <iostream>
#include <math.h>
#include "Motorcycle.h"
using namespace std;


int main(){
    Motorcycle m1(1, 1, 5, 10);
    double T = 0;
    double t = 0.01;
    m1.setAs(0.4);
    for (int i=0; i<10; i++){
        cout << "s[" << T << "]=(" << m1.getX() << ", " << m1.getY() << ")";
        cout << "v[" << T << "]=(" << m1.getVx() << ", " << m1.getVy() << ")";
        cout << endl;
        T = T+t;
        m1.Integrate(t); 
    }
}
