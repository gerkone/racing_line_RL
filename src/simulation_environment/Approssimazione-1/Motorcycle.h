#ifndef MOTORCYCLE
#define MOTORCYCLE

class Motorcycle{
private:
double _x;   //x position
double _y;   //y position
double _vx = 0;  //x velocity
double _vy = 0;  //y velocity
double _ax = 0;  //x accelleration
double _ay = 0;  //y accelleration
double _t = 0;   //theta
double _av = 0;  //angular velocity
double _aa = 0;  //angular accelleration
double _a  = 0;   //inclination angle

double _as = 0;  //accellerator stroke level

double _m;   //mass
double _r;   //wheel radius
double _fm;  //motor maximum force
double _b;   //air friction constant

public:
    Motorcycle(double m, double r, double fm, double b, double x=0, double y=0){
        _x = x;
        _y = y;
        _m = m;
        _r = r;
        _fm = fm;
        _b = b;
    }
    double calcAngularAccellerationMotorStroke();
    double calcAngularAccellerationAirFriction();
    void Integrate(double t);
    
    double getX(){return _x;}
    double getY(){return _y;}
    double getVx(){return _vx;}
    double getVy(){return _vy;}
    double getV(){return sqrt(_vx*_vx + _vy*_vy);}
    double getAx(){return _ax;}
    double getAy(){return _ay;}
    double getT(){return _t;}
    double getAv(){return _av;}
    double getAa(){return _aa;}
    double getA(){return _a;}
    double getAs(){return _as;}
    double getM(){return _m;}
    double getR(){return _r;}
    double getFm(){return _fm;}
    double getB(){return _b;}
    
    void setAs(double as){_as = as;}
};

double Motorcycle::calcAngularAccellerationMotorStroke(){
    return (2*_as*_fm)/(_m*_r);
}
double Motorcycle::calcAngularAccellerationAirFriction(){
    return -(2*_b*getV())/(3*_r*_m);
}
void Motorcycle::Integrate(double t){
    _aa = calcAngularAccellerationMotorStroke() + calcAngularAccellerationAirFriction();
    _av = t*_aa + _av;
    _t = t*_av + _t;
    double alpha;
    if (_vx != 0){
        alpha = atan(_vy/_vx);
    }else{
        alpha = 0; 
    }
    double temps = t*_av*_r;
    double tempx = temps*cos(alpha);
    double tempy = temps*sin(alpha);
    _vx = abs(_x - tempx)/t;
    _vy = abs(_y - tempy)/t;
    _x = tempx;
    _y = tempy;
}
#endif
