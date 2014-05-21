import sys
import exceptions
import geometry
import fileIO

#
# Classes
#


class Particle(geometry.Point):
    def __init__(self, x, y, pType=""):
        geometry.Point.__init__(self, x, y)
        self.__skipped = False
        self.pType = pType
        
    def skip(self, skipped):
        self.__skipped = skipped
    
    def is_skipped(self):
        return self.__skipped
    
    skipped = property(is_skipped, skip)            

    def __isWithinHole(self, syn):
        """  Determine whether self is inside a profile hole
        """                
        for h in syn.holeli:
            if self.isWithinPolygon(h):
                return True
        return False

    def __isWithinShell(self, profile, opt):
        return (self.distToPath != None 
                and abs(self.distToPath) <= 
                        geometry.toPixelUnits(opt.shell_width, profile.pixelwidth))

    def determineStuff(self, profile, opt):
        if self.__isWithinHole(profile):
            if self.pType == "particle": # no warning for random and grid points
                ProfileWarning(profile, "Particle at %s located within a hole\n"
                                    "   => skipping" % self)
            self.skipped = True
            profile.nskipped[self.pType] += 1
            return        
        distToPath = self.perpendDist(profile.path, posloc=profile.posloc)
        if distToPath == None:
            if self.pType == "particle":        
                ProfileWarning(profile, "Unable to project on path \n"
                                    "   => skipping particle at"
                                    " %s" % self)
            self.skipped = True
            profile.nskipped[self.pType] += 1            
            return
            self.distToPath = sys.maxint
            self.lateralDistPath = sys.maxint
            self.normLateralDistPath = sys.maxint
        else:
            self.distToPath = distToPath
            self.lateralDistPath = self.lateralDist(profile.path)
            self.normLateralDistPath = self.lateralDistPath / (profile.path.length() / 2.0)
        self.isAssociatedWithPath = (self.perpendDist(profile.path, 
                                                     posloc=None, 
                                                     doNotCareIfOnOrOffSeg=True)
                                     <= geometry.toPixelUnits(opt.spatial_resolution,
                                                     profile.pixelwidth))
        self.isWithinShell = self.__isWithinShell(profile, opt)

    def determineNearestNeighbour(self, profile, opt):
        if not self.isAssociatedWithPath:
            self.nearestNeighbour = None
            return
        mindist = float(sys.maxint)
        for p in profile.pli:
            if p is not self and p.isAssociatedWithPath:
                if self.dist(p) < mindist:
                    mindist = self.dist(p)
        if not mindist < float(sys.maxint):
            self.nearestNeighbour = None
        else:
            self.nearestNeighbour = mindist
                

    def perpendDist(self, m, negloc=geometry.Point(None, None),
                    posloc=geometry.Point(None, None),
                    doNotCareIfOnOrOffSeg=False):        
        """" Calculate distance from the particle to path m;
             negloc is a point defined to have a negative distance
             to the path; posloc is a point defined to have a positive 
             distance to the path; if neither negloc nor posloc is 
             defined, absolute distance is returned.             
        """
        mindist = float(sys.maxint)
        on_M = False
        for n in range(0, len(m) - 1):
            if (m[n].x != -1) and (m[n+1].x != -1):
                on_this_seg, d = self.distToSegment(m, n)
                if d <= mindist:      # smallest distance so far...
                    mindist = d
                    if on_this_seg or doNotCareIfOnOrOffSeg: 
                        on_M = True   # least distance and "on" segment (not
                                      # completely true; see distToSegment())
                    else:
                        on_M = False      # least distance but "off" segment
        if not on_M:
            return None     
        # If polarity (posloc or negloc) is defined, we say that particles 
        # on the positive side of the path have positive distances to the 
        # path, while other particles have negative distances. To 
        # determine this, we count the number of path segments 
        # dissected by the line between the particle and negloc (posloc). 
        # Even (odd) number => the particle and negloc (posloc) are on the same
        # same side of the path; odd number => different side.
        if negloc and self.segmentCrossingNumber(m, negloc) % 2 == 0:
            mindist = -mindist
        elif posloc and self.segmentCrossingNumber(m, posloc) % 2 != 0:
            mindist = -mindist
        return mindist      
    
    def lateralDist(self, path):
        """ Determine lateral distance to center of path. If distance > 1, 
            the projection of the particle is on the extension of path.
        """
        subPath = geometry.SegmentedPath()
        # need node only
        foo, seg_path_center = path.centerPoint().projectOnPathOrEndnode(path) 
        project, seg_project = self.projectOnPathOrEndnode(path)
        subPath.extend([project, path.centerPoint()])
        if seg_path_center < seg_project: 
            subPath.reverse()
        for n in range(min(seg_path_center, seg_project) + 1, 
                       max(seg_path_center, seg_project)):
            subPath.insert(len(subPath)-1, path[n])
        L = subPath.length()
        return L           
    
       
class ProfileData:
    def __init__(self, inputfn, opt):
        self.inputfn = inputfn
        self.opt = opt
        self.holeli = []
        self.pli = []
        self.gridli = []
        self.randomli = []
        self.nskipped = {"particle":0, "random":0, "grid": 0}            
        self.warnflag = False
        self.errflag = False             

    def process(self, opt):
        """ Parse profile data from a file and determine distances
        """
        try:
            self.__parse()
            self.__checkPath()
            sys.stdout.write("Determining stuff...\n")
            for p in self.pli:
                p.determineStuff(self, opt)
            self.pli = [p for p in self.pli if not p.skipped]
            for g in self.gridli:
                g.determineStuff(self, opt)
            self.gridli = [g for g in self.gridli if not g.skipped]            
            for r in self.randomli:
                r.determineStuff(self, opt)
            self.randomli = [r for r in self.randomli if not r.skipped]
            for pType in ("particle", "random", "grid"):
                if (pType == "random" and not opt.useRandom) or (pType == "grid" and not opt.useGrid):
                    continue
                pTypeStr = "particles" if pType == "particle" else pType + " points"
                sys.stdout.write("  Number of %s skipped: %d\n"
                                 % (pTypeStr, self.nskipped[pType]))
            #for p in self.pli:
            #    p.determineNearestNeighbour(self)
            if opt.stop_requested:
                return
            sys.stdout.write("Done.\n")
            if opt.individualProfileOutput:
                self.__saveResults(opt)
        except ProfileError, (self, msg):
            sys.stdout.write("Error: %s\n" % msg)
            self.errflag = True
          
            
    def __parse(self):
        """ Parse profile data from input file 
        """
        sys.stdout.write("\nParsing '%s':\n" % self.inputfn)
        li = fileIO.readFile(self.inputfn)
        if not li:
            raise ProfileError(self, "Could not open input file")
        while li:
            s = li.pop(0).replace("\n","").strip()
            if s.split(" ")[0].upper() == "IMAGE":
                self.src_img = s.split(" ")[1]
            elif s.split(" ")[0].upper() == "PROFILE_ID":
                try:
                    self.ID = int(s.split(" ")[1])
                except IndexError, ValueError:
                    ProfileWarning(self, "Profile ID not defined or invalid")
            elif s.split(" ")[0].upper() == "COMMENT":
                try:
                    self.comment = s.split(" ", 1)[1]
                except IndexError:
                    self.comment = ''
            elif s.split(" ")[0].upper() == "PIXELWIDTH":
                try: 
                    self.pixelwidth = float(s.split(" ")[1])
                    self.metric_unit = s.split(" ")[2]
                except IndexError, ValueError:
                    raise ProfileError(self, 
                                       "PIXELWIDTH is not a valid number")
            elif s.split(" ")[0].upper() == "POSLOC":
                try:
                    x, y = s.split(" ", 1)[1].split(", ")
                    self.posloc = geometry.Point(float(x), float(y))
                except IndexError, ValueError:
                    raise ProfileError(self, "POSLOC not valid")
            elif s.upper() == "PATH":
                self.path = geometry.SegmentedPath(self.__getCoords(li, "path"))
            elif s.upper() == "HOLE":
                self.holeli.append(geometry.SegmentedPath(self.__getCoords(li, "hole")))
            elif s.upper() == "PARTICLES":
                pli = self.__getCoords(li, "particle")
                for p in pli: 
                    self.pli.append(Particle(p.x, p.y, pType="particle"))
            elif s.upper() == "GRID":
                gridli = self.__getCoords(li, "grid")
                for g in gridli: 
                    self.gridli.append(Particle(g.x, g.y, pType="grid"))                    
            elif s.upper() == "RANDOM_POINTS":
                randomli = self.__getCoords(li, "random")
                for r in randomli: 
                    self.randomli.append(Particle(r.x, r.y, pType="random"))                                        
            elif s[0] != "#":          # unless specifically commented out           
                ProfileWarning(self, "Unrecognized string '" + s + 
                                    "' in input file")
        # Now, let's see if everything was found
        self.__checkParsedData()

    def __checkParsedData(self):
        """ See if the synapse data was parsed correctly, and print info on the
            parsed data to standard output.            
        """
        try:
            self.src_img
        except AttributeError:
            self.src_img = "N/A"
        sys.stdout.write("  Source image: %s\n" % self.src_img)
        try:
            self.ID
        except AttributeError:
            self.ID = "N/A"
        sys.stdout.write("  Profile ID: %s\n" % self.ID)
        try:
            self.comment
        except AttributeError:
            self.comment = ""
        sys.stdout.write("  Comment: %s\n" % self.comment)
        try:
            sys.stdout.write("  Pixel width: %.2f " % self.pixelwidth)
        except AttributeError:
            raise ProfileError(self, 
                               "No valid pixel width found in input file")
        try:
            sys.stdout.write("%s\n" % self.metric_unit)
        except AttributeError:
            raise ProfileError(self, "Metric unit not found in input file")
        try:
            self.posloc
            sys.stdout.write("  Polarity: defined\n")
        except AttributeError:
            self.posloc = geometry.Point(None, None)
            sys.stdout.write("  Polarity: not defined\n")
        try: 
            self.path[1]
        except (IndexError, AttributeError):
            raise ProfileError(self, "No path coordinates found in input file")
        else:
            sys.stdout.write("  Path nodes: %d\n"
                             % len(self.path))
        sys.stdout.write("  Holes: %d\n" % len(self.holeli))
        sys.stdout.write("  Particles: %d\n" % len(self.pli))
        try: 
            self.gridli[0]
        except (IndexError, AttributeError):
            pass
        else:
            sys.stdout.write("  Grid specified.\n")
            self.opt.useGrid = True
        try: 
            self.randomli[0]
        except (IndexError, AttributeError):
            pass
        else:
            sys.stdout.write("  Random points specified.\n")
            self.opt.useRandom = True
        for n, h in enumerate(self.holeli):
            if not h.isSimplePolygon():
                raise ProfileError(self, 
                                   "Profile hole %d is not a simple polygon" 
                                    % (n+1))
            for n2, h2 in enumerate(self.holeli[n+1:]):
                if h.overlapsPolygon(h2):
                    raise ProfileError(self, 
                                       "Profile hole %d overlaps with hole %d "
                                       % (n+1, n+n2+2))                                    
                 
        
    def __checkPath(self):
        """ Make sure that path does not intersect with itself
        """        
        for n1 in range(0, len(self.path)-3):
            for n2 in range(0, len(self.path)-1):
                if n1 not in (n2, n2+1) and n1+1 not in (n2, n2+1):
                    if geometry.segmentIntersection(self.path[n1], self.path[n1+1],
                                           self.path[n2], self.path[n2+1]):
                        raise ProfileError(self, "Path invalid (crossing "
                                                 "vertices)")
        sys.stdout.write("  Path contains no crossing vertices.\n")
 

    def __getCoords(self, strli, coordType=""):
        """ Pop point coordinates from list strli.
            When an element of strli is not a valid point,
            a warning is issued.
        """
        pointli = []
        s = strli.pop(0).replace("\n","").replace(" ","").strip()
        while s != "END":
            try:
                p = geometry.Point(float(s.split(",")[0]), float(s.split(",")[1]))
                if pointli and (p == pointli[-1] or 
                                (coordType == 'particle' and p in pointli)):
                    sys.stdout.write("Duplicate %s coordinates %s: skipping "
                                     "2nd instance\n" % (coordType, p))
                else:
                    pointli.append(Particle(p.x, p.y, pType=coordType))                    
            except ValueError:
                if s[0] != "#":
                    ProfileWarning(self, "'%s' not valid %s coordinates" 
                                   % (s, coordType))
                else:
                    pass 
            s = strli.pop(0).replace("\n","").strip()
        # For some reason, sometimes the endnodes have the same coordinates;
        # in that case, delete the last endnode to avoid division by zero
        if (len(pointli) > 1) and (pointli[0] == pointli[-1]): 
            del pointli[-1]                                            
        return pointli        


    def shape(self, flat_threshold = 0.98):
        """Classify the shape of a path as follows: draw a line L between
           the end nodes of the path. The shape is then classified as:  
              - "convex"  if L is completely positive,
              - "concave" if L is completely negative,
              - "u-like"  if L is completely on one side but polarity is undefined
              - "w-like"  if L crosses the path an even number of times, 
              - "s-like"  if L crosses the path an odd number of times, 
              - "flat"    if L is (almost) 'collinear' with the path.

              flat_threshold is the minimum fraction of the length of the path
              that the length of L may be for L to be considered 'collinear'
              with the path and hence the path considered flat. Default
              flat_threshold is 0.98.
        """
        L = geometry.SegmentedPath([self.path[0], self.path[-1]])
        # skip end segments of the path, because L will always intersect with
        # the end nodes but not with the rest of those segments
        path_shortened = [self.path[n] for n in range(1, len(self.path)-2)] 
        c = L.centerPoint()
        cdist = Particle(c.x, c.y).perpendDist(self.path, posloc=self.posloc)
        xnum = self.path[0].segmentCrossingNumber(path_shortened, 
                                                  self.path[-1])
        if xnum == 0:
            if cdist < 0: 
                return "concave"
            elif cdist > 0:
                if self.posloc: 
                    return "convex"
                else:
                    return "u-like"
            else:  # don't know about this... if collinear, what is xnum? 
                 return "flat"
        elif L.length()/self.path.length() > flat_threshold:
            return "flat"
        elif xnum % 2 == 0: 
            return "w-like"
        else: 
            return "s-like"

    
    def curvatureCentroid(self):
        """ Return a measure of synaptic curvature based on the centroid of the
            polygon formed when drawing a line between the end nodes of the 
            path. The curvature is defined as the distance between the centroid 
            and its projection on the path, divided by the area of the path. 
            Curvature < 0  if the centroid is postsynaptic (the synapse is 
            "convex" as defined by Profile.shape()); curvature > 0  if the 
            centroid is not postsynaptic (synapse is "concave"). Curvature is 
            not defined for synapses with "flat", "w-like" or "s-like" shapes.            
        """
        if self.shape() in ("flat", "w-like", "s-like"):
            return None
        c = self.path.centroid()
        return (1000*Particle(c.x, c.y).perpendDist(self.path, 
                                                    posloc=self.psdloc) /
                self.path.area())

              
    def curvatureDevFromStraight(self):
        """ Return a measure of synaptic curvature based on the deviation of 
            the path from a straight line; defined as the normalized
            difference in length between path and the straight line between 
            the end nodes of path. Return value is in the range [0,1[ where a  
            lower value corresponds to a flatter synapse. 
        """
        L = geometry.SegmentedPath([self.path[0], self.path[-1]])
        return 1 - L.length() / self.path.length()         
                                                       

# end of class Profile        
        
class OptionData:
    def __init__(self):
        self.input_file_list = []
        self.spatial_resolution = 25
        self.shell_width = 200
        self.outputs = {'profile summary': True, 'particle summary': True,
                        'random summary': True, 'session summary': True}
        self.gridSummary = True
        self.interparticleSummary = False
        self.individualProfileOutput = False
        self.output_file_format = "excel"
        self.output_filename_ext = ".xls"
        self.input_filename_ext = ".d2p"
        self.output_filename_suffix = ''
        self.output_filename_other_suffix = ''
        self.output_filename_date_suffix = True
        self.output_filename_use_other_suffix = False
        self.csv_delimiter = 'comma'
        self.action_if_output_file_exists = 'overwrite'
        self.output_dir = ''
        self.useRandom = False
        self.useGrid = False
# end of class OptionData


class ProfileError(exceptions.Exception):
    def __init__(self, profile, msg):
        self.args = (profile, msg + ".")

def ProfileWarning(profile, msg):
    """ Issue a warning
    """
    sys.stdout.write("Warning: %s.\n" % msg)
    profile.warnflag = True      

def ProfileMessage(profile, msg):
    """ Show a message
    """
    sys.stdout.write("%s.\n" % msg)