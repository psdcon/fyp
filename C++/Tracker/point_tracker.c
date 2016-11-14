/* Example 10-1. Pyramid Lucas-Kanade optical flow code

   ************************************************** */

#include <cv.h>
#include <cxcore.h>
#include <highgui.h>
#include <stdio.h>
#include <time.h>

clock_t start,end;
double cpu_time_used;

const int MAX_CORNERS = 100;

int   corner_count;
CvPoint2D32f *cornersA, *cornersB;
IplImage *imgA, *imgB, *eig_image, *tmp_image;
int   win_size;
char features_found[ MAX_CORNERS ];
float feature_errors[ MAX_CORNERS ];
int t_initialize=0 ;
int t_clear=0 ;
int t_pause=0;

void InitializeTracking ();
void TrackbarInitialize (int);
void TrackbarClear (int);
void TrackbarFunction (int){};
void MouseNewPoint(int event, int x, int y, int flags, void* param );

int main(int argc, char** argv) {
  /*********************************************************************************************
  First we get the video
  *********************************************************************************************/
  CvCapture* capture;   //CvCapture is the structure used by openCv to handle with video

  if (argc == 1)    //If we have provided an argument we will load a video, if not we will take the image from a webcam
        capture = cvCreateCameraCapture(-1);
  else
    capture = cvCreateFileCapture(argv [1]);

  if (!capture) return -1;  //Check that everything is ok

  double fps = cvGetCaptureProperty (
        capture,
        CV_CAP_PROP_FPS
    );
  if (fps == 0) fps=15; //Sometimes the webcam gives 0 fps, but the real value is 15 fps
  /*********************************************************************************************
  Prepare the variables
  *********************************************************************************************/
  IplImage* bgrFrame= cvQueryFrame (capture);
  CvSize      img_sz    = cvGetSize( bgrFrame );
  imgA = cvCreateImage(img_sz,IPL_DEPTH_8U,1);
  imgB = cvCreateImage(img_sz,IPL_DEPTH_8U,1);
  IplImage* imgPoints = cvCreateImage(img_sz,IPL_DEPTH_8U,3);
  cvCvtColor(bgrFrame,imgA,CV_RGB2GRAY);
  win_size = 10;

  eig_image = cvCreateImage( img_sz, IPL_DEPTH_32F, 1 );
  tmp_image = cvCreateImage( img_sz, IPL_DEPTH_32F, 1 );
  /*********************************************************************************************
  Window sizes
  *********************************************************************************************/
  int width = bgrFrame->width;
  int height = bgrFrame->height;
  int widthMax = 600;   //You cand adjust this values to fit better in your computer
  int heightMax = 600;
  if (width>height)
  {
    height = height * widthMax / width ;
    width = widthMax;
  }
  else
  {
    width = width * heightMax / height;
    height = heightMax;
  }
  IplImage *imgTemp = cvCreateImage(cvSize(width,height),IPL_DEPTH_8U,3);
  cvNamedWindow("LKpyr_OpticalFlow",0);
  cvResizeWindow("LKpyr_OpticalFlow",width,height);
  cvMoveWindow("LKpyr_OpticalFlow",1300,20);
  cvSetMouseCallback( "LKpyr_OpticalFlow",  MouseNewPoint);

  cvNamedWindow("Points",CV_WINDOW_AUTOSIZE);
  cvMoveWindow("Points",1300+width,20);

  cvNamedWindow("Controls",CV_WINDOW_AUTOSIZE);
  cvMoveWindow("Controls",1300,80+height);
  cvCreateTrackbar("Initialize","Controls",&t_initialize,1,TrackbarInitialize);
  cvCreateTrackbar("Clear","Controls",&t_clear,1,TrackbarClear);
  cvCreateTrackbar("Pause","Controls",&t_pause,1,TrackbarFunction);

  // The first thing we need to do is get the features
  // we want to track.
  //
  InitializeTracking();


  CvSize pyr_sz = cvSize( imgA->width+8, imgB->height/3 );
  IplImage* pyrA = cvCreateImage( pyr_sz, IPL_DEPTH_32F, 1 );
  IplImage* pyrB = cvCreateImage( pyr_sz, IPL_DEPTH_32F, 1 );

  /*********************************************************************************************
  While loop
  *********************************************************************************************/
  while(1)
  {
    start=clock();
    if (t_pause==0)
    {
      bgrFrame= cvQueryFrame (capture);
      if (!bgrFrame) break;
      cvCvtColor(bgrFrame,imgB,CV_RGB2GRAY);
    }
    else
    {
      cvCopyImage(imgA,imgB);
    }

    // Call the Lucas Kanade algorithm
    CvPoint2D32f* cornersB        = new CvPoint2D32f[ MAX_CORNERS ];
    cvCalcOpticalFlowPyrLK(   //Calculates an optical flow for a sparse feature set using the iterative Lucas-Kanade method with pyramids.
      imgA,     //Initial image
      imgB,     //Final image
      pyrA,     //buffer for pyramid image
      pyrB,     //buffer for pyramid image
      cornersA,   //prevPts – Vector of 2D points for which the flow needs to be found. The point coordinates must be single-precision floating-point numbers.
      cornersB,   //nextPts – Output vector of 2D points (with single-precision floating-point coordinates) containing the calculated new positions of input features in the second image. When OPTFLOW_USE_INITIAL_FLOW flag is passed, the vector must have the same size as in the input.
      corner_count, //Points in cornersA
      cvSize( win_size,win_size ),    //Size of the window for local coherent motion
      5,          //If 0 pyramids are not used
      features_found,   //Status. 1 if the point is in the second image, 0 if not
      feature_errors,   //track_error. Diference between the two points
      cvTermCriteria( CV_TERMCRIT_ITER | CV_TERMCRIT_EPS, 20, .3 ),
      0
    );

    // Now make some image of what we are looking at:
    cvZero(imgPoints);
    for( int i=0; i<corner_count; i++ ) {
      if( features_found[i]==0|| feature_errors[i]>550 ) continue;
      CvPoint p0 = cvPoint(
      cvRound( cornersA[i].x ),
      cvRound( cornersA[i].y )
      );
      CvPoint p1 = cvPoint(
      cvRound( cornersB[i].x ),
      cvRound( cornersB[i].y )
      );
      CvScalar color=CV_RGB(0,255,0);
      cvLine( imgPoints, p0, p1, color,1 );
      cvLine( bgrFrame, p0, p1, color,1 );
      cvCircle( bgrFrame, p1,
        2, //Radius
        color, //Color
        -1); //Filled
      cvCircle( imgPoints, p1,
        2, //Radius
        color, //Color
        -1); //Filled

    }
    cvShowImage("LKpyr_OpticalFlow",bgrFrame); //We can't do the resize becouse the mouse fails
    cvResize(imgPoints,imgTemp); cvShowImage("Points",imgTemp);
    cvCopyImage(imgB,imgA);
    delete(cornersA);
    cornersA=cornersB;

    /*********************************************************************************************
    Adjust the waiting time to play the videos at the correct speed
    *********************************************************************************************/
    end=clock();
    int tiempoEspera;
    if (fps != 15)  //When we deal with a webcam the best option is to wait a short time
    {
      cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC*1000;
      int milis = int (cpu_time_used);
      printf("Tiempo invertido = %d  ms",milis);
      int tiempoFrame = int (1000/fps);
      printf("    Tiempo frame = %d  ms\n",tiempoFrame);
      if (tiempoFrame>=milis) tiempoEspera = tiempoFrame-milis;
      else
      {
        bgrFrame= cvQueryFrame (capture);
        tiempoEspera=milis-tiempoFrame;
        printf("\n");
        while(tiempoEspera>tiempoFrame)
        {
          bgrFrame= cvQueryFrame (capture);
          tiempoEspera = tiempoEspera-tiempoFrame;
          printf("\n");
        }
      }
      if (tiempoEspera == 0) tiempoEspera = 1;
    }
    else tiempoEspera = 10;
    if (cvWaitKey(tiempoEspera) == 27) break;
  }

  cvReleaseImage( &imgB);
  cvReleaseImage( &imgA);
  cvDestroyWindow( "LKpyr_OpticalFlow" );
  cvDestroyWindow( "Controls" );
  cvDestroyWindow( "Points" );
  if (cornersA) delete(cornersA);
  if (cornersB) delete(cornersB);

}

/*********************************************************************************************
  Look for good points to track
*********************************************************************************************/
void InitializeTracking ()
{
  corner_count = MAX_CORNERS;
  printf("Puntos pedidos = %d  \n",corner_count);
  if (cornersA) delete(cornersA);
  cornersA = new CvPoint2D32f[ MAX_CORNERS ];
  cvGoodFeaturesToTrack(
    imgA,         //Input 8-bit or floating-point 32-bit, single-channel image.
    eig_image,        //The parameter is ignored. Same size floating-point 32-bit, single-channel image.
    tmp_image,        //The parameter is ignored. Same size floating-point 32-bit, single-channel image.
    cornersA,       //Output vector of detected corners. Array of 32bit points
    &corner_count,      //Maximum number of corners to return. It is overwritten by the number of points returned
    0.01,         //Parameter characterizing the minimal accepted quality of image corners. The parameter value is multiplied by the best corner quality measure, which is the minimal eigenvalue (see cornerMinEigenVal() ) or the Harris function response (see cornerHarris() ). The corners with the quality measure less than the product are rejected. For example, if the best corner has the quality measure = 1500, and the qualityLevel=0.01 , then all the corners with the quality measure less than 15 are rejected.
    5.0,          //Minimum possible Euclidean distance between the returned corners.
    0,            //mask – Optional region of interest.
    3,            //Size of an average block for computing a derivative covariation matrix over each pixel neighborhood.
    0,            //useHarrisDetector – Parameter indicating whether to use a Harris detector
    0.04          //Free parameter of the Harris detector.
  );
  /*
  cvGoodFeaturesToTrack
  The function finds the most prominent corners in the image or in the specified image region, as described in [Shi94]:
  Function calculates the corner quality measure at every source image pixel using the cornerMinEigenVal() or cornerHarris() .
  Function performs a non-maximum suppression (the local maximums in 3 x 3 neighborhood are retained).
  The corners with the minimal eigenvalue less than  are rejected.
  The remaining corners are sorted by the quality measure in the descending order.
  Function throws away each corner for which there is a stronger corner at a distance less than maxDistance.
  IMPORTANT:
  The function can be used to INITIALIZE a point-based tracker of an object.
  */
  printf("Puntos devueltos = %d  \n",corner_count);
  cvFindCornerSubPix(         //Refines the corner locations.
    imgA,             //image – Input image.
    cornersA,           //Initial coordinates of the input corners and refined coordinates provided for output.
    corner_count,         //count - how many points are to compute
    cvSize(win_size,win_size),    //winSize – Half of the side length of the search window. For example, if winSize=Size(5,5) , then a  search window 11x11 is used.
    cvSize(-1,-1),          //zeroZone – Half of the size of the dead region in the middle of the search zone over which the summation in the formula below is not done. It is used sometimes to avoid possible singularities of the autocorrelation matrix. The value of (-1,-1) indicates that there is no such a size.
    cvTermCriteria(CV_TERMCRIT_ITER|CV_TERMCRIT_EPS,20,0.03)  //criteria – Criteria for termination of the iterative process of corner refinement. That is, the process of corner position refinement stops either after criteria.maxCount iterations or when the corner position moves by less than criteria.epsilon on some iteration.
  );
  /*
  The function iterates to find the sub-pixel accurate location of corners or radial saddle points, as shown on the figure below.
  */
}

/*********************************************************************************************
  Look for good points to track
*********************************************************************************************/
void TrackbarInitialize (int)
{
  if (t_initialize == 1)
  {
    InitializeTracking();
    cvSetTrackbarPos("Initialize","Controls",0);
    t_initialize =0;
  }
}

/*********************************************************************************************
  Add new points to track
*********************************************************************************************/
void MouseNewPoint(int event, int x, int y, int flags, void* param )
{

  IplImage* image = (IplImage*) param;

  switch( event ) {
    /*case CV_EVENT_MOUSEMOVE:
  case CV_EVENT_LBUTTONUP:*/
    case CV_EVENT_LBUTTONDOWN: {
    if (corner_count<MAX_CORNERS)
    {
      cornersA[corner_count]=cvPoint2D32f(x,y);
      printf("Nuevo punto %d en x = %d y = %d\n",corner_count,x,y);
      corner_count++;
    }
    else
    {
      bool found=false;
      int i=0;
      while( (i<MAX_CORNERS) && (!found) )
      {
        if (features_found[i]==0)
        {
          cornersA[i]=cvPoint2D32f(x,y);
          printf("Nuevo punto %d en x = %d y = %d\n",i,x,y);
          found=true;
          break;
        }
        i++;
      }
      if (!found) printf("No hay espacio para mas puntos\n");
    }
    }
    break;
  }
}
/*********************************************************************************************
  Clear all the points
*********************************************************************************************/
void TrackbarClear (int)
{
  if (t_clear == 1)
  {
    if (cornersA) delete(cornersA);
    if (cornersB) delete(cornersB);
    cornersA = new CvPoint2D32f[ MAX_CORNERS ];
    corner_count=0;
    cvSetTrackbarPos("Clear","Controls",0);
    t_clear=0;
  }
}