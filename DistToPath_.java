/*
    plugin : DistToPath_.java
    date   : January 22, 2010
    author : Max Larsson
    e-mail : m.d.larsson@medisin.uio.no

    This ImageJ plugin is for use in conjunction with DistToPath.py.
    
    Some bits were copied from the IP_Demo.java plugin included with ImageJ.
    
    Copyright 2010 Max Larsson <m.d.larsson@medisin.uio.no>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.   
      
*/

import java.awt.*;
import java.awt.event.*;
import java.awt.Font.*;
import java.lang.Object.*;
import java.lang.Integer.*;
import java.io.*;
import java.util.Random;
import ij.*;
import ij.process.*;
import ij.io.*;
import ij.gui.*;
import ij.plugin.frame.*;
import ij.plugin.filter.*;
import ij.measure.*;
import ij.text.*;



interface OptionsDTP {
    Color pathCol = Color.blue;
    Color particleCol = Color.yellow;
    Color poslocCol = Color.green;
    Color randomPointCol = Color.magenta;
    Color gridCol = Color.orange;
    Color holeCol = Color.red;           
}

public class DistToPath_ extends PlugInFrame implements OptionsDTP, ActionListener {
    
    Panel panel;
    static Frame instance;
    static Frame infoFrame;
    GridBagLayout infoPanel;
    Label profile_nLabel;
    Label pathnLabel;
    Label pnLabel;    
    Label poslocLabel;
    Label holenLabel;            
    Label gridPlacedLabel;
    Label randomPlacedLabel;        
    Label commentLabel;
    Label scaleLabel;
    ProfileDataDTP profile;
    ImagePlus imp;
    boolean UseRGB = true;        

    
    public DistToPath_() {
        super("DistToPath");
        if (instance != null) {
            instance.toFront();
            return;
        }
        instance = this;
        profile = new ProfileDataDTP();
        IJ.register(DistToPath_.class);
        setLayout(new FlowLayout());
        setBackground(SystemColor.control);
        panel = new Panel();
        panel.setLayout(new GridLayout(0, 1, 4, 1));
        panel.setBackground(SystemColor.control);    
        panel.setFont(new Font("Helvetica", 0, 12));
        addButton("Save profile");
        addButton("Clear profile");
        panel.add(new Label(""));
        panel.add(new Label("Define selection as:"));                
        addButton("Path");
        addButton("Particle list");
        addButton("Hole");        
        addButton("Positive polarity");
        panel.add(new Label(""));     
        addButton("Place random points");
        addButton("Place grid");       
        panel.add(new Label(""));        
        panel.add(new Label("Other:"));                
        addButton("Add comment");
        addButton("Set profile n");
        addButton("Options...");        
        add(panel);
        pack();
        setVisible(true);
        infoFrame = new Frame("Profile info");
        infoPanel = new GridBagLayout();
        infoFrame.setFont(new Font("Helvetica", 0, 10));
        infoFrame.setBackground(SystemColor.control);
        infoFrame.setLocation(0, instance.getLocation().x + instance.getSize().height + 3);
        infoFrame.setIconImage(instance.getIconImage());
        infoFrame.setResizable(false);
        GridBagConstraints c = new GridBagConstraints();    
        c.fill = GridBagConstraints.BOTH;
        c.weightx = 1.0;
        c.gridwidth = 1;
        addStaticInfoLabel("Profile n:", Label.LEFT, c);
        c.gridwidth = GridBagConstraints.REMAINDER;
        profile_nLabel = new Label(IJ.d2s(profile.ntot, 0), Label.RIGHT);
        addVarInfoLabel(profile_nLabel, c);                
        c.gridwidth = 1;                
        addStaticInfoLabel("Path nodes:", Label.LEFT, c);
        c.gridwidth = GridBagConstraints.REMAINDER;
        pathnLabel = new Label(IJ.d2s(profile.pathn, 0), Label.RIGHT);
        addVarInfoLabel(pathnLabel, c);
        c.gridwidth = 1;
        addStaticInfoLabel("Particles:", Label.LEFT, c);
        c.gridwidth = GridBagConstraints.REMAINDER;
        pnLabel = new Label(IJ.d2s(profile.pn, 0), Label.RIGHT);
        addVarInfoLabel(pnLabel, c);
        c.gridwidth = 1;        
        addStaticInfoLabel("Holes:", Label.LEFT, c);
        c.gridwidth = GridBagConstraints.REMAINDER;
        holenLabel = new Label(IJ.d2s(profile.holen, 0), Label.RIGHT);
        addVarInfoLabel(holenLabel, c);             
        c.gridwidth = 1;
        addStaticInfoLabel("Positive polarity:", Label.LEFT, c);
        c.gridwidth = GridBagConstraints.REMAINDER;
        poslocLabel = new Label("N/D", Label.RIGHT);
        addVarInfoLabel(poslocLabel, c);
        c.gridwidth = 1;        
        addStaticInfoLabel("Grid:", Label.LEFT, c);
        c.gridwidth = GridBagConstraints.REMAINDER;
        gridPlacedLabel = new Label("no", Label.RIGHT);
        addVarInfoLabel(gridPlacedLabel, c);
        c.gridwidth = 1;
        addStaticInfoLabel("Random points:", Label.LEFT, c);
        c.gridwidth = GridBagConstraints.REMAINDER;    
        randomPlacedLabel = new Label("no", Label.RIGHT);
        addVarInfoLabel(randomPlacedLabel, c);                                                
        c.gridwidth = 1;                
        addStaticInfoLabel("Pixel width:", Label.LEFT, c);               
        c.gridwidth = GridBagConstraints.REMAINDER;
        scaleLabel = new Label("N/D", Label.RIGHT);
        addVarInfoLabel(scaleLabel, c);                                             
        c.gridwidth = 1;
        addStaticInfoLabel("Comment:", Label.LEFT, c);                               
        c.gridwidth = GridBagConstraints.REMAINDER;
        commentLabel = new Label("", Label.RIGHT);
        addVarInfoLabel(commentLabel, c);
        infoFrame.setLayout(infoPanel);
        infoFrame.pack();
        infoFrame.setSize(instance.getSize().width, infoFrame.getSize().height);
        infoFrame.setVisible(true);
        instance.requestFocus();
    }
    
    void addButton(String label) {
        Button b = new Button(label);
        b.addActionListener(this);
        panel.add(b);
    }

    void addStaticInfoLabel(String name, int alignment, GridBagConstraints c) {
         Label l = new Label(name, alignment);
         infoPanel.setConstraints(l, c);
         infoFrame.add(l);
    }   
    
    void addVarInfoLabel(Label l, GridBagConstraints c) {
         infoPanel.setConstraints(l, c);
         infoFrame.add(l);
    }   
            
    PolygonRoi getPolylineRoi(ImagePlus imp) {
        Roi roi = imp.getRoi();
        if (roi == null || roi.getType() != roi.POLYLINE) {
            IJ.error("DistToPath", "Segmented line selection required.");
            return null;
        } else {
            return (PolygonRoi) roi; 
        }
    }

    PolygonRoi getPolygonRoi(ImagePlus imp) {
        Roi roi = imp.getRoi();
        if (roi == null || roi.getType() != roi.POLYGON) {
            IJ.error("DistToPath", "Polygon selection required.");
            return null;
        } else {
            return (PolygonRoi) roi; 
        }
    }        
    
    PolygonRoi getPointRoi(ImagePlus imp) {
        Roi roi = imp.getRoi();
        if (roi == null || roi.getType() != roi.POINT) {
            IJ.error("DistToPath", "Point selection required.");
            return null;
        } else {
            return (PolygonRoi) roi;
        }
    }
                
    void updateInfoPanel() {
        int i, psdntot = 0;
        double pixelwidth;
        String unit;
            
        profile_nLabel.setText(IJ.d2s(profile.ntot, 0));
        pathnLabel.setText(IJ.d2s(profile.pathn, 0));
        pnLabel.setText(IJ.d2s(profile.pn, 0));
        holenLabel.setText(IJ.d2s(profile.holen, 0));              
        if (profile.poslocx != -1 && profile.poslocy != -1) {
            poslocLabel.setText(IJ.d2s(profile.poslocx, 0) +
                                ", " + IJ.d2s(profile.poslocy, 0));    
        }
        if (profile.gridPlaced) {
            gridPlacedLabel.setText("yes");    
        }
        if (profile.randomPlaced) {
            randomPlacedLabel.setText("yes");
        }                        
        Calibration c = imp.getCalibration();
        if (c.getUnit() == "micron") {
            pixelwidth = c.pixelWidth * 1000;
            unit = "nm";
        } else {
            pixelwidth = c.pixelWidth;
            unit = c.getUnit();
        }
        scaleLabel.setText(IJ.d2s(pixelwidth, 2) + " " + unit);
        commentLabel.setText(profile.comment);                
        infoFrame.setVisible(true);
    }
    
            
    public void actionPerformed(ActionEvent e) {
        PolygonRoi p;
        int i, j, k, w, h;
        int offsetx, offsety, xInterval=128, yInterval=128;                
        String s;
                
        imp = WindowManager.getCurrentImage();
        if (imp == null) {
            IJ.beep();
            IJ.showStatus("No image");
            return;
        }
        String command = e.getActionCommand();
        if (command == null) {
            return; 
        }
        if (UseRGB && imp.getType() != ImagePlus.COLOR_RGB) {
            imp.setProcessor(imp.getTitle(), imp.getProcessor().convertToRGB());
        }                
        if (command.equals("Save profile")) {
            if (profile.dirty == false) {
                IJ.showMessage("Nothing to save.");
            } else {
                boolean saved = profile.save(imp);
                if (saved) {
                    profile.clear(imp);
                }
            }
        }
        if (command.equals("Clear profile")) {
            if (profile.dirty) {
                YesNoCancelDialog d = new YesNoCancelDialog(imp.getWindow(), 
                    "DistToPath", "Save current\nprofile?");
                if (d.yesPressed()) {
                    profile.dirty = !profile.save(imp);
                } else if (!d.cancelPressed()) {
                    profile.dirty = false;
                }                                
            }
            if (!profile.dirty) {
                profile.clear(imp);
                IJ.showStatus("Profile cleared.");
            }   
        }   
        if (command.equals("Path")) {
            if (!profile.isSameImage(imp) ||
                profile.isDefined(imp, profile.pathn, 0, "Path")) { 
                return;
            }
            if ((p = getPolylineRoi(imp)) != null) {
                profile.pathn = p.getNCoordinates();
                int[] x = p.getXCoordinates();
                int[] y = p.getYCoordinates();
                profile.pathx = new int[profile.pathn]; 
                profile.pathy = new int[profile.pathn];     
                Rectangle r = p.getBoundingRect();
                profile.pathBoundingRect = r;
                for (i = 0; i < profile.pathn; i++) {
                    profile.pathx[i] = x[i] + r.x;
                    profile.pathy[i] = y[i] + r.y;
                }
                if (UseRGB) { 
                    imp.setColor(pathCol);
                } else { 
                    imp.setColor(Color.black);
                }                                                
                p.drawPixels();
                profile.dirty = true;
            }
        }   
        if (command.equals("Particle list")) {
            if (!profile.isSameImage(imp) ||
                profile.isDefined(imp, profile.pn, 0, "Particles")) { 
                return;
            }
            if ((p = getPointRoi(imp)) != null) {
                profile.pn = p.getNCoordinates();
                int[] x = p.getXCoordinates();
                int[] y = p.getYCoordinates();
                profile.px = new float[profile.pn]; 
                profile.py = new float[profile.pn];     
                Rectangle r = p.getBoundingRect();
                for (i = 0; i < profile.pn; i++) {
                    profile.px[i] = (float) x[i] + r.x;
                    profile.py[i] = (float) y[i] + r.y;
                }
                if (UseRGB) { 
                    imp.setColor(particleCol);
                } else { 
                    imp.setColor(Color.white);
                }                                                
                p.drawPixels();
                imp.setColor(Color.black);                                
                profile.dirty = true;
            }   
        }
        if (command.equals("Positive polarity")) {
            if (!profile.isSameImage(imp) ||
                profile.isDefined(imp, profile.poslocx, -1, "Polarity")) { 
                return;
            }
            if ((p = getPointRoi(imp)) != null) {                           
                if (p.getNCoordinates() > 1) {
                    IJ.error("DistToPath", "Could not define polarity:\nMore than one point selected.");
                    return;
                }
                int[] x = p.getXCoordinates();
                int[] y = p.getYCoordinates();
                Rectangle r = p.getBoundingRect();
                profile.poslocx = x[0] + r.x;
                profile.poslocy = y[0] + r.y;
                if (UseRGB) { 
                    imp.setColor(poslocCol);
                } else { 
                    imp.setColor(Color.black);
                }                                
                //p.drawPixels();
                imp.getProcessor().drawLine(profile.poslocx-5, profile.poslocy, 
                                            profile.poslocx+5, profile.poslocy);
                imp.getProcessor().drawLine(profile.poslocx, profile.poslocy-5, 
                                            profile.poslocx, profile.poslocy+5);                
                profile.dirty = true;
                imp.setColor(Color.black);                
            }   
        } 
        if (command.equals("Hole")) {
            if (!profile.isSameImage(imp)) { 
                return;
            }
            if ((p = getPolygonRoi(imp)) != null) {
                profile.holeli[profile.holen].pathn = p.getNCoordinates();
                int[] x = p.getXCoordinates();
                int[] y = p.getYCoordinates();
                profile.holeli[profile.holen].pathx = new int[profile.holeli[profile.holen].pathn]; 
                profile.holeli[profile.holen].pathy = new int[profile.holeli[profile.holen].pathn];     
                Rectangle r = p.getBoundingRect();
                for (i = 0; i < profile.holeli[profile.holen].pathn; i++) {
                    profile.holeli[profile.holen].pathx[i] = x[i] + r.x;
                    profile.holeli[profile.holen].pathy[i] = y[i] + r.y;
                }
                if (UseRGB) { 
                    imp.setColor(holeCol);
                } else { 
                    imp.setColor(Color.white);
                }                
                p.drawPixels();
                imp.setColor(Color.black);
                profile.holen++;
                profile.dirty = true;
            }
       }                              
       if (command.equals("Place random points")) {
            if (!profile.isSameImage(imp) ||
                 profile.isPlaced(imp, profile.randomPlaced, "Random points")) { 
                return;
            }                    
            Random rnd = new Random();
            profile.randompx = new int[profile.randompn]; 
            profile.randompy = new int[profile.randompn];
            if (UseRGB) { 
                imp.setColor(randomPointCol);
            } else { 
                imp.setColor(Color.white);
            }
            for (i = 0; i < profile.randompn; i++) {
                w = rnd.nextInt(imp.getWidth()-1)+1;
                h = rnd.nextInt(imp.getHeight()-1)+1;
                profile.randompx[i] = w;
                profile.randompy[i] = h;
                imp.getProcessor().drawLine(w-5,  h, w+5, h);
                imp.getProcessor().drawLine(w, h-5, w, h+5);
            }
            profile.randomPlaced = true;
        }              
        if (command.equals("Place grid")) {
            if (!profile.isSameImage(imp) ||
                 profile.isPlaced(imp, profile.gridPlaced, "Grid")) { 
                return;
            }             
            profile.gridn = profile.gridHoriz * profile.gridVert;
            profile.gridx = new int[profile.gridn];
            profile.gridy = new int[profile.gridn];
            xInterval = (int) java.lang.Math.floor(imp.getWidth() / profile.gridHoriz);
            yInterval = (int) java.lang.Math.floor(imp.getHeight() / profile.gridVert);
            if (profile.gridRandomOffset) {
                Random rnd = new Random();
                offsetx = rnd.nextInt(xInterval);
                offsety = rnd.nextInt(yInterval);
            }
            else {
                offsetx = (int) java.lang.Math.floor(xInterval / 2);
                offsety = (int) java.lang.Math.floor(yInterval / 2);
            }
            k = 0;
            if (UseRGB) { 
                imp.setColor(gridCol);
            } else { 
                imp.setColor(Color.white);
            }            
            for (i = 0; i < profile.gridHoriz; i++) {
                w = offsetx + i * xInterval;
                //imp.getProcessor().drawLine(w,  0, w, imp.getHeight());                
                for (j = 0; j < profile.gridVert; j++) {
                    // w = offsetx + i * xInterval;
                    h = offsety + j * yInterval;
                    profile.gridx[k] = w;  
                    profile.gridy[k++] = h;
                    imp.getProcessor().drawLine(w-5,  h, w+5, h);
                    imp.getProcessor().drawLine(w, h-5, w, h+5);
                    //imp.getProcessor().drawLine(0,  h, imp.getWidth(), h);                    
                }
            }
            imp.setColor(Color.black);
            profile.gridPlaced = true;
        }        
        if (command.equals("Set profile n")) {
            s = IJ.getString("Set profile n", IJ.d2s(profile.ntot, 0));
            profile.ntot = java.lang.Integer.parseInt(s);
        }     
        if (command.equals("Add comment")) {
            s = IJ.getString("Comment: ", profile.comment);
            if (s != "") {
                profile.comment = s;
                profile.dirty = true;
            }
        }
        if (command.equals("Options...")) {
            GenericDialog gd = new GenericDialog("Options");
            gd.setInsets(0, 0, 0);            
            gd.addCheckbox("Use RGB colour", UseRGB);            
            gd.addMessage("Grid properties:");
            gd.addNumericField("Horizontal n:", profile.gridHoriz, 0);
            gd.addNumericField("Vertical n:", profile.gridVert, 0);
            gd.addCheckbox("Random offset", profile.gridRandomOffset);
            gd.addMessage("");
            gd.addMessage("Random particles:");
            gd.addNumericField("Random particle n:", profile.randompn, 0);
            gd.showDialog();
            if (gd.wasCanceled())
                return;
            UseRGB = gd.getNextBoolean();
            profile.gridHoriz = (int) gd.getNextNumber();
            if (profile.gridHoriz <=0) {
                IJ.error("Horizontal n must be larger than 0. Reverting to default value (8).");
                profile.gridHoriz = 8;
            }
            profile.gridVert = (int) gd.getNextNumber();            
            if (profile.gridVert <=0) {
                IJ.error("Vertical n must be larger than 0. Reverting to default value (8).");
                profile.gridVert = 8;
            }            
            profile.gridRandomOffset = gd.getNextBoolean();
            profile.randompn = (int) gd.getNextNumber();
            if (profile.gridVert <=0) {
                IJ.error("Random point n must be larger than 0. Reverting to default value (40).");
                profile.randompn = 40;
            }                        
        }                        
        updateInfoPanel();
        imp.updateAndDraw();
        IJ.showStatus("");
    }

    public void processWindowEvent(WindowEvent e) {
        super.processWindowEvent(e);
        if (e.getID()==WindowEvent.WINDOW_CLOSING) {
            infoFrame.dispose();
            infoFrame = null;
            instance = null;
        }
    }

} // end of DistToPath_

class HoleDataDTP {
    int[] pathx, pathy;
    int pathn;
    
    public String coords(int n) {
        return(IJ.d2s(this.pathx[n], 0) + ", "+ IJ.d2s(this.pathy[n], 0));
    }
    
    HoleDataDTP () {
        this.pathn = 0;
    }
    
}


class ProfileDataDTP implements OptionsDTP {
    boolean dirty;
    HoleDataDTP[] holeli;        
    int[] pathx, pathy;
    float[] px, py;
    int[] randompx, randompy;
    int[] gridx, gridy;    
    int i, n, ntot, pathn, pn, holen, randompn, gridn, poslocx, poslocy;
    int gridHoriz = 10, gridVert = 10;
    boolean gridPlaced, gridRandomOffset, randomPlaced;        
    int imgID, prevImgID;
    String ID, comment, prevImg;
    Rectangle pathBoundingRect;    
    int MAXHOLES = 50;    
    
    ProfileDataDTP () {
        this.n = 0;
        this.ntot = 1;
        this.prevImg = "";
        this.imgID = 0;
        this.dirty = false;
        this.pathn = 0;
        this.pn = 0;
        this.poslocx = -1;
        this.poslocy = -1;
        this.holen = 0;
        this.holeli = new HoleDataDTP[this.MAXHOLES];
        for (i=0; i<this.MAXHOLES; i++) {  
            this.holeli[i] = new HoleDataDTP();
        }        
        this.randomPlaced = false;
        this.randompn = 200;
        this.gridPlaced = false;
        this.gridRandomOffset = true;
        this.gridn = 0;                        
        this.comment = "";
        this.ID = "";
    }
    

    public String showPathCoords(int n) {
        return(IJ.d2s(this.pathx[n], 0) + ", "+ IJ.d2s(this.pathy[n], 0));
    }

    public String showPCoords(int n) {
        return(IJ.d2s(this.px[n], 2) + ", " + IJ.d2s(this.py[n], 2));
    }
    public String showRandomCoords(int n) {
        return(IJ.d2s(this.randompx[n], 0) + ", " + IJ.d2s(this.randompy[n], 0));
    }
    public String showGridCoords(int n) {
        return(IJ.d2s(this.gridx[n], 0) + ", " + IJ.d2s(this.gridy[n], 0));
    }    
    

    public boolean isSameImage(ImagePlus imp) {
        if (!this.dirty || this.imgID == 0) {
            this.imgID = imp.getID();
            return true;
        } else if (this.imgID == imp.getID()) {
            return true;
        } else {
            IJ.error("DistToPath", "All measurements must be performed on the same " + 
                                   "image.");
            return false;
        }
    }       
        
    public boolean isDefined(ImagePlus imp, int var_to_check, int not_defined_val, String warnstr) {
        if (var_to_check != not_defined_val) {
            YesNoCancelDialog d = new YesNoCancelDialog(imp.getWindow(), 
                             "DistToPath", "Warning:\n" + warnstr + " already defined.\nOverwrite?");
            if (!d.yesPressed()) {
                return true;
            }
        }
        return false;
    }

    public boolean isPlaced(ImagePlus imp, boolean var_to_check, String warnstr) {
        if (var_to_check) {
            YesNoCancelDialog d = new YesNoCancelDialog(imp.getWindow(), 
                             "Synapse07", "Warning:\n" + warnstr + " already placed.\nOverwrite?");
            if (!d.yesPressed()) {
                return true;
            }
        }
        return false;
    }
    
    private boolean CheckProfileDataDTP(ImagePlus imp) {
        String[] warnstr;
        int i, nwarn = 0;
        
        warnstr = new String[9];
        Calibration c = imp.getCalibration();
        if (c.getUnit().equals(" ")) {
            IJ.error("DistToPath", "Error: The scale has not been set.");
            return false;
        }
        if (this.pathn == 0) {
            IJ.error("DistToPath", "Error: Path not defined.");
            return false;
        }
        if (this.poslocx == -1) {
            warnstr[nwarn++] = "Positive location not defined.";
        }                          
        if (this.pn == 0) {
            warnstr[nwarn++] = "No particle coordinates defined.";
        }          
        if (nwarn > 0) {
            for (i = 0; i < nwarn; i++) {
                YesNoCancelDialog d = new YesNoCancelDialog(imp.getWindow(), 
                    "DistToPath", "Warning:\n" + warnstr[i] + "\nContinue anyway?");
                if (!d.yesPressed()) {
                    return false;
                }
            }
        }       
        return true;
    }
        
    
    public boolean save(ImagePlus imp) {
        int i, p, k;
        double pixelwidth;
        String s, unit;
        
        IJ.showStatus("Saving profile...");
        if (!CheckProfileDataDTP(imp)) {
            return false;
        }
        Calibration c = imp.getCalibration();
        if (c.pixelWidth != c.pixelHeight) {
            IJ.showMessage("Warning: pixel aspect ratio is not 1.\n" +
                           "Only pixel WIDTH is used.");
        }
        try {
            if (imp.getTitle() != this.prevImg) {
                    this.n = 0;
                    this.prevImg = imp.getTitle();
            } 
            this.n++;
            s = IJ.getString("Profile ID: ", IJ.d2s(this.ntot, 0));
            if (s != "") {
                this.ID = s;
            }
            SaveDialog sd = new SaveDialog("Save profile", 
                                           imp.getTitle() + "." + 
                                           IJ.d2s(this.n, 0), ".d2p");
            if (sd.getFileName() == null) {
                this.n--;                                            
                return false;
            }
            PrintWriter outf = 
                new PrintWriter(
                    new BufferedWriter(
                        new FileWriter(sd.getDirectory() + 
                                       sd.getFileName())));
            outf.println("IMAGE " + imp.getTitle());                    
            outf.println("PROFILE_ID " + this.ID);
            outf.println("COMMENT " + this.comment);
            if (c.getUnit() == "micron") {
                pixelwidth = c.pixelWidth * 1000;
                unit = "nm";
            } else {
                pixelwidth = c.pixelWidth;
                unit = c.getUnit();
            }
            outf.println("PIXELWIDTH " + IJ.d2s(pixelwidth) + " " + unit);
            if (this.poslocx != -1 && this.poslocy != -1) {
                outf.println("POSLOC " + IJ.d2s(this.poslocx, 0) + ", " 
                             + IJ.d2s(this.poslocy, 0));                    
            } else {
                outf.println("POSLOC ");
            }
            outf.println("PATH");
            if (this.pathn > 0) { 
                for (i = 0; i < this.pathn; i++) {
                    outf.println("  " + this.showPathCoords(i));
                }
            }
            outf.println("END");            
            for (k = 0; k < this.holen; k++) {
                outf.println("HOLE");
                for(i=0; i < this.holeli[k].pathn; i++)
                    outf.println("  " + this.holeli[k].coords(i));
                outf.println("END");  
            }                           
            outf.println("PARTICLES");
            if (this.pn > 0) { 
                for (i = 0; i < this.pn; i++) {
                    outf.println("  " + this.showPCoords(i));
                }
            }
            outf.println("END");
            if (this.randomPlaced) {            
                outf.println("RANDOM_POINTS");
                for (i = 0; i < this.randompn; i++) {
                        outf.println("  " + this.showRandomCoords(i));
                }
                outf.println("END");
            }                        
            if (this.gridPlaced) {
                outf.println("GRID");
                for (i=0; i < this.gridn; i++) {
                    outf.println("  " + this.showGridCoords(i));
                }
                outf.println("END");
            }                        
            outf.close();                    
        } catch (Exception e) {
            return false;
        }
        writeIDtext(imp);                
        this.ntot++;        
        SaveDialog sd = new SaveDialog("Save analyzed image", 
                                       imp.getShortTitle(), 
                                       ".a.tif");
        if (sd.getFileName() != null) {
            FileSaver saveTiff = new FileSaver(imp);
            saveTiff.saveAsTiff(sd.getDirectory() + sd.getFileName());
        }                                             
        return true;
    }       

    private void writeIDtext(ImagePlus imp) {
        TextRoi idLabel;
        int k, i, locx, locy;
        
        idLabel = new TextRoi(0, 0, imp);
        for (i=0; i < this.ID.length(); i++) {
            idLabel.addChar(this.ID.charAt(i));
        }
        locy = this.pathBoundingRect.y - idLabel.getBounds().height - 5;
        locx = this.pathBoundingRect.x;
        if (locy < 0) {
            locy = this.pathBoundingRect.y + this.pathBoundingRect.height + 5;
            if (locy + idLabel.getBounds().height > imp.getHeight()) {
                     locy = this.pathBoundingRect.y;
                locx = this.pathBoundingRect.x - idLabel.getBounds().width - 5;
                if (locx < 0) {
                   locx = this.pathBoundingRect.x + this.pathBoundingRect.width;
                }                     
            }
        }
        if (locx + idLabel.getBounds().width > imp.getWidth()) {
            locx = imp.getWidth() - idLabel.getBounds().width - 5;
        }
        idLabel.setLocation(locx, locy);
        idLabel.setFont(idLabel.getFont(), 24, idLabel.getStyle());
        if (imp.getType() == ImagePlus.COLOR_RGB) { 
            imp.setColor(pathCol);
        } else { 
            imp.setColor(Color.white);
        }
        idLabel.drawPixels(); 
        imp.setColor(Color.black);        
    }        
    
    
    public void clear(ImagePlus imp) {
        int k; 
        
        this.dirty = false;
        this.pathn = 0;
        this.pn = 0;
        this.poslocx = -1;
        this.poslocy = -1;
        this.holen = 0;
        this.randomPlaced = false;
        this.gridPlaced = false;        
        for(k = 0; k < this.MAXHOLES; k++) {
            this.holeli[k]  = new HoleDataDTP();; 
        }                
        this.comment = "";
        this.ID = "";
        Analyzer a = new Analyzer(imp);
        a.getResultsTable().reset();
        a.updateHeadings();
    }
} // end of DistToPath
