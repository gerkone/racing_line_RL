#ifndef MOTORCYCLE
#define MOTORCYCLE

#define INCREEMENTODELTA 0.05
#define INCREEMENTOACCELERATION 0.01
#define MAXACCELERATION 1.0

class Car{
private:
double _x = 0;   //x position
double _y = 0;   //y position
double _dotx = 0;  //x velocity
double _doty = 0;  //y velocity
double _beta = 0; //angle of the velocity from the car assex
double _delta = 0; //angle of the front wheel from the car assex
double _psi = 0; //angle of the car assex from the x assex
double _dotpsi = 0;

double _Ma = 0; //Motor accelleration
public:
    Car(double Ma, double delta){_Ma = Ma;_delta = delta;}
    Car(){}

    void Integrate(double t);
    void print();

    double getX(){return _x;}
    double getY(){return _y;}
    double getPsi(){return _psi;}
    double getDelta(){return _delta;}

    void setMa(double Ma){_Ma = Ma;}
    void setDelta(double delta){_delta = delta;}

    void storgiDx(){
        if (_delta>-1){
            _delta = _delta - INCREEMENTODELTA;
        }
    }
    void storgiSx(){
        if (_delta<1){
            _delta = _delta + INCREEMENTODELTA;
        }
    }
    void accelate(){
      _Ma +=INCREEMENTOACCELERATION;
      if (_Ma>MAXACCELERATION){
        _Ma = MAXACCELERATION;
      }
    }
    void stroke(){
      _Ma -=INCREEMENTOACCELERATION;
      if (_Ma<0){
        _Ma = 0;
      }
    }
};

void Car::Integrate(double dt){
    double dotX, dotY;
    dotX = _dotx*cos(_psi)+_doty*sin(_psi);
    dotY = _doty*cos(_psi)-_dotx*sin(_psi);
    dotX = _Ma*dt + dotX;
    _dotx = dotX*cos(_psi) - dotY*sin(_psi);
    _doty = dotX*sin(_psi) + dotY*cos(_psi);
    _beta = atan(tan(_delta)/2);
    double v = sqrt(_dotx*_dotx + _doty*_doty);
    _dotpsi = v/1*sin(_beta);
    _psi = _dotpsi*dt + _psi;
    _dotx = v*cos(_beta+_psi);
    _doty = v*sin(_beta+_psi);
    _x = _dotx*dt + _x;
    _y = _doty*dt + _y;
}

void Car::print(){
    cout<<"--------------------------"<<endl;
    cout<<"(X, Y) = ("<<_x<<", "<<_y<<")"<<endl;
    cout<<"(VX, VY) = ("<<_dotx<<", "<<_doty<<")"<<endl;
    cout<<"delta = ("<<_delta<<")"<<endl;
    cout<<"beta = ("<<_beta<<")"<<endl;
    cout<<"psi = ("<<_psi<<") Vpsi = ("<<_dotpsi<<")"<<endl;
    cout<<"Ma = ("<<_Ma<<")"<<endl;
    cout<<"--------------------------"<<endl;
}
#endif
