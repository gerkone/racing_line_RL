#version 430
layout(location=0) in vec3 position;
uniform mat4 mv_matrix;
uniform mat4 proj_matrix;

out vec4 varyingColor;

void main(void){
  gl_Position = proj_matrix * mv_matrix * vec4(position, 1.0);
  varyingColor = vec4(position.x, position.y*0.5, position.z, 1.0) *0.009 + vec4(0.2, 0.2, 0.2, 0.2);
}
