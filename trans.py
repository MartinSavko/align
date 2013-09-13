DevDouble TrueTrans_FP;(a*((100.0 * ((FP_Gap_X * FP_Gap_Z) / Area))^2)) + (b * (100.0 * ((FP_Gap_X * FP_Gap_Z) / Area))) + c;FP_Gap_X=sqrt(Area * (-b+sqrt((b^2) - (4.0*a*(c-TrueTrans_FP))))/(2.0*a*100*Ratio));FP_Gap_Z=sqrt(Area*Ratio*(-b + sqrt((b^2) - (4.0*a*(c-TrueTrans_FP)))) / (2.0*a * 100.0))


Vars:
TrueTrans_FP
FP_Gap_X: I11-MA-C02/EX/FENT_H.1/gap
FP_Gap_Z: I11-MA-C02/EX/FENT_V.1/gap
Area: I11-MA-C00/EX/FPCONSTPARSER/FP_Area_FWHM
Ratio: I11-MA-C00/EX/FPCONSTPARSER/Ratio_FP_Gap

a: I11-MA-C00/EX/CONSTANTES/PolyFP_a
b: I11-MA-C00/EX/CONSTANTES/PolyFP_b
c: I11-MA-C00/EX/CONSTANTES/PolyFP_c
I0: I11-MA-CX1/EX/MD2-PUBLISHER/I0
I: I11-MA-C04/DT/XBPM_DIODE.1/intensity


IONames:
DevDouble TrueTrans_FP;(a*((100.0 * ((FP_Gap_X * FP_Gap_Z) / Area))^2)) 
                       + (b * (100.0 * ((FP_Gap_X * FP_Gap_Z) / Area))) 
                       + c;
FP_Gap_X=sqrt(Area * (-b+sqrt((b^2) - (4.0*a*(c-TrueTrans_FP))))/(2.0*a*100*Ratio));
FP_Gap_Z=sqrt(Area*Ratio*(-b + sqrt((b^2) - (4.0*a*(c-TrueTrans_FP)))) / (2.0*a * 100.0))


OutputNames:
DevDouble FP_Area,FP_Gap_X * FP_Gap_Z
DevDouble T,100.0 * ((FP_Gap_X * FP_Gap_Z) / Area)
DevDouble Gap_X,sqrt(Area * (-b+sqrt((b^2) - (4.0*a*(c-TrueTrans_FP))))/(2.0*a*100*Ratio))
DevDouble Gap_Z,sqrt(Area*Ratio*(-b + sqrt((b^2) - (4.0*a*(c-TrueTrans_FP)))) / (2.0*a * 100.0))
DevDouble I_Trans, (I/I0)*100
DevDouble Current_Ratio, FP_Gap_Z/FP_Gap_X


#Python reimplementation
#Constants:
Ration = 
FP_Gap_X = sqrt(Area * ( -b + sqrt(4. * a * (c - TrueTrans_FP)))/(2. * a * 
x = FP_Gap_X * FP_Gap_Z / Area
TrueTrans_FP = 100. * a * x**2 + 100 * b * x + c