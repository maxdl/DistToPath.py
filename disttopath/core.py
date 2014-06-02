# -*- coding: utf-8 -*-

import sys
import exceptions
import geometry
import file_io

#
# Classes
#


class Particle(geometry.Point):
    def __init__(self, x, y, ptype=""):
        geometry.Point.__init__(self, x, y)
        self.__skipped = False
        self.ptype = ptype
        self.dist_to_path = None
        self.lateral_dist_path = None
        self.norm_lateral_dist_path = None
        self.is_assoc_with_path = None
        self.is_within_shell = None
        self.nearest_neighbour = geometry.Point()
        
    def skip(self, skipped):
        self.__skipped = skipped
    
    def is_skipped(self):
        return self.__skipped
    
    skipped = property(is_skipped, skip)            

    def __is_within_hole(self, syn):
        """  Determine whether self is inside a profile hole
        """                
        for h in syn.holeli:
            if self.is_within_polygon(h):
                return True
        return False

    def __is_within_shell(self, profile, opt):
        return (self.dist_to_path is not None
                and abs(self.dist_to_path) <=
                geometry.to_pixel_units(opt.shell_width, profile.pixelwidth))

    def determine_stuff(self, profile, opt):
        if self.__is_within_hole(profile):
            if self.ptype == "particle":  # don't warn if random or grid points
                profile_warning(profile,
                                "Particle at %s located within a hole\n"
                                "   => skipping" % self)
            self.skipped = True
            profile.nskipped[self.ptype] += 1
            return        
        dist_to_path = self.perpend_dist(profile.path, posloc=profile.posloc)
        if dist_to_path is None:
            if self.ptype == "particle":
                profile_warning(profile, "Unable to project on path \n"
                                         "   => skipping particle at"
                                         " %s" % self)
            self.skipped = True
            profile.nskipped[self.ptype] += 1
            return
        else:
            self.dist_to_path = dist_to_path
            self.lateral_dist_path = self.lateral_dist(profile.path)
            self.norm_lateral_dist_path = (self.lateral_dist_path /
                                          (profile.path.length() / 2.0))
        self.is_assoc_with_path = (self.
                                   perpend_dist(profile.path,
                                                #posloc=None,
                                                dont_care_if_on_or_off_seg=True)
                                     <= geometry.
                                        to_pixel_units(opt.spatial_resolution,
                                                       profile.pixelwidth))
        self.is_within_shell = self.__is_within_shell(profile, opt)

    def get_nearest_neighbour(self, profile):
        if not self.is_assoc_with_path:
            self.nearest_neighbour = None
            return
        mindist = float(sys.maxint)
        for p in profile.pli:
            if p is not self and p.isAssociatedWithPath:
                if self.dist(p) < mindist:
                    mindist = self.dist(p)
        if not mindist < float(sys.maxint):
            self.nearest_neighbour = None
        else:
            self.nearest_neighbour = mindist
    
       
class ProfileData:
    def __init__(self, inputfn, opt):
        self.id = None
        self.inputfn = inputfn
        self.src_img = None
        self.opt = opt
        self.holeli = []
        self.pli = []
        self.gridli = []
        self.randomli = []
        self.nskipped = {"particle": 0, "random": 0, "grid": 0}
        self.comment = ""
        self.pixelwidth = None
        self.metric_unit = ""
        self.posloc = geometry.Point()
        self.path = geometry.SegmentedPath()
        self.warnflag = False
        self.errflag = False             

    def process(self, opt):
        """ Parse profile data from a file and determine distances
        """
        try:
            self.__parse()
            self.__check_path()
            sys.stdout.write("Determining stuff...\n")
            for p in self.pli:
                p.determine_stuff(self, opt)
            self.pli = [p for p in self.pli if not p.skipped]
            for g in self.gridli:
                g.determine_stuff(self, opt)
            self.gridli = [g for g in self.gridli if not g.skipped]            
            for r in self.randomli:
                r.determine_stuff(self, opt)
            self.randomli = [r for r in self.randomli if not r.skipped]
            for ptype in ("particle", "random", "grid"):
                if ((ptype == "random" and not opt.use_random) or
                        (ptype == "grid" and not opt.use_grid)):
                    continue
                ptypestr = ("particles"
                            if ptype == "particle" else ptype + " points")
                sys.stdout.write("  Number of %s skipped: %d\n"
                                 % (ptypestr, self.nskipped[ptype]))
            #for p in self.pli:
            #    p.get_nearest_neighbour(self)
            if opt.stop_requested:
                return
            sys.stdout.write("Done.\n")
            #if opt.individualProfileOutput:
            #    self.__saveResults(opt)
        except ProfileError, (self, msg):
            sys.stdout.write("Error: %s\n" % msg)
            self.errflag = True

    def __parse(self):
        """ Parse profile data from input file 
        """
        sys.stdout.write("\nParsing '%s':\n" % self.inputfn)
        li = file_io.read_file(self.inputfn)
        if not li:
            raise ProfileError(self, "Could not open input file")
        while li:
            s = li.pop(0).replace("\n", "").strip()
            if s.split(" ")[0].upper() == "IMAGE":
                self.src_img = s.split(" ")[1]
            elif s.split(" ")[0].upper() == "PROFILE_ID":
                try:
                    self.id = int(s.split(" ")[1])
                except (IndexError, ValueError):
                    profile_warning(self, "Profile id not defined or invalid")
            elif s.split(" ")[0].upper() == "COMMENT":
                try:
                    self.comment = s.split(" ", 1)[1]
                except IndexError:
                    self.comment = ''
            elif s.split(" ")[0].upper() == "PIXELWIDTH":
                try: 
                    self.pixelwidth = float(s.split(" ")[1])
                    self.metric_unit = s.split(" ")[2]
                except (IndexError, ValueError):
                    raise ProfileError(self, 
                                       "PIXELWIDTH is not a valid number")
            elif s.split(" ")[0].upper() == "POSLOC":
                try:
                    x, y = s.split(" ", 1)[1].split(", ")
                    self.posloc = geometry.Point(float(x), float(y))
                except (IndexError, ValueError):
                    raise ProfileError(self, "POSLOC not valid")
            elif s.upper() == "PATH":
                self.path = geometry.SegmentedPath(self.__get_coords(li,
                                                                     "path"))
            elif s.upper() == "HOLE":
                self.holeli.append(
                    geometry.SegmentedPath(self.__get_coords(li, "hole")))
            elif s.upper() == "PARTICLES":
                pli = self.__get_coords(li, "particle")
                for p in pli: 
                    self.pli.append(Particle(p.x, p.y, ptype="particle"))
            elif s.upper() == "GRID":
                gridli = self.__get_coords(li, "grid")
                for g in gridli: 
                    self.gridli.append(Particle(g.x, g.y, ptype="grid"))
            elif s.upper() == "RANDOM_POINTS":
                randomli = self.__get_coords(li, "random")
                for r in randomli: 
                    self.randomli.append(Particle(r.x, r.y, ptype="random"))
            elif s[0] != "#":          # unless specifically commented out           
                profile_warning(self, "Unrecognized string '" + s +
                                    "' in input file")
        # Now, let's see if everything was found
        self.__check_parsed_data()

    def __check_parsed_data(self):
        """ See if the synapse data was parsed correctly, and print info on the
            parsed data to standard output.            
        """
        if self.src_img is None:
            self.src_img = "N/A"
        sys.stdout.write("  Source image: %s\n" % self.src_img)
        if self.id is None:
            self.id = "N/A"
        sys.stdout.write("  Profile id: %s\n" % self.id)
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
        if self.posloc:
            sys.stdout.write("  Polarity: defined\n")
        else:
            sys.stdout.write("  Polarity: not defined\n")
        if not self.path:
            raise ProfileError(self, "No path coordinates found in input file")
        else:
            sys.stdout.write("  Path nodes: %d\n" % len(self.path))
        sys.stdout.write("  Holes: %d\n" % len(self.holeli))
        sys.stdout.write("  Particles: %d\n" % len(self.pli))
        if self.gridli: 
            sys.stdout.write("  Grid specified.\n")
            self.opt.use_grid = True
        if self.randomli: 
            sys.stdout.write("  Random points specified.\n")
            self.opt.use_random = True
        for n, h in enumerate(self.holeli):
            if not h.is_simple_polygon():
                raise ProfileError(self, 
                                   "Profile hole %d is not a simple polygon" 
                                    % (n + 1))
            for n2, h2 in enumerate(self.holeli[n + 1:]):
                if h.overlaps_polygon(h2):
                    raise ProfileError(self, 
                                       "Profile hole %d overlaps with hole %d "
                                       % (n + 1, n + n2 + 2))                                    
                         
    def __check_path(self):
        """ Make sure that path does not intersect with itself
        """        
        for n1 in range(0, len(self.path) - 3):
            for n2 in range(0, len(self.path) - 1):
                if n1 not in (n2, n2 + 1) and n1 + 1 not in (n2, n2 + 1):
                    if geometry.segment_intersection(self.path[n1],
                                                     self.path[n1 + 1],
                                                     self.path[n2],
                                                     self.path[n2 + 1]):
                        raise ProfileError(self, "Path invalid (crossing "
                                                 "vertices)")
        sys.stdout.write("  Path contains no crossing vertices.\n")
 
    def __get_coords(self, strli, coord_type=""):
        """ Pop point coordinates from list strli.
            When an element of strli is not a valid point,
            a warning is issued.
        """
        pointli = []
        s = strli.pop(0).replace("\n", "").replace(" ", "").strip()
        while s != "END":
            try:
                p = geometry.Point(float(s.split(",")[0]), 
                                   float(s.split(",")[1]))
                if pointli and (p == pointli[-1] or 
                                (coord_type == 'particle' and p in pointli)):
                    sys.stdout.write("Duplicate %s coordinates %s: skipping "
                                     "2nd instance\n" % (coord_type, p))
                else:
                    pointli.append(Particle(p.x, p.y, ptype=coord_type))
            except ValueError:
                if s[0] != "#":
                    profile_warning(self, "'%s' not valid %s coordinates"
                                    % (s, coord_type))
                else:
                    pass 
            s = strli.pop(0).replace("\n", "").strip()
        # For some reason, sometimes the endnodes have the same coordinates;
        # in that case, delete the last endnode to avoid division by zero
        if (len(pointli) > 1) and (pointli[0] == pointli[-1]): 
            del pointli[-1]                                            
        return pointli        

    def shape(self, flat_threshold=0.98):
        """Classify the shape of a path as follows: draw a line l between
           the end nodes of the path. The shape is then classified as:  
            - "convex"  if l is completely positive,
            - "concave" if l is completely negative,
            - "u-like"  if l is completely on one side but polarity is undefined
            - "w-like"  if l crosses the path an even number of times,
            - "s-like"  if l crosses the path an odd number of times,
            - "flat"    if l is (almost) 'collinear' with the path.

              flat_threshold is the minimum fraction of the length of the path
              that the length of l may be for l to be considered 'collinear'
              with the path and hence the path considered flat. Default
              flat_threshold is 0.98.
        """
        l = geometry.SegmentedPath([self.path[0], self.path[-1]])
        # skip end segments of the path, because l will always intersect with
        # the end nodes but not with the rest of those segments
        path_shortened = [self.path[n] for n in range(1, len(self.path) - 2)]
        c = l.center_point()
        cdist = Particle(c.x, c.y).perpend_dist(self.path, posloc=self.posloc)
        xnum = self.path[0].segment_crossing_number(path_shortened,
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
        elif l.length() / self.path.length() > flat_threshold:
            return "flat"
        elif xnum % 2 == 0: 
            return "w-like"
        else: 
            return "s-like"

    def curvature_centroid(self):
        """ Return a measure of path curvature based on the centroid of the
            polygon formed when drawing a line between the end nodes of the 
            path. The curvature is defined as the distance between the centroid 
            and its projection on the path, divided by the area of the path. 
            Curvature < 0  if the centroid is positive (the path is "convex"
            as defined by Profile.shape()); curvature > 0  if the centroid is
            negative (path is "concave"). Curvature is not defined for paths
            with "flat", "w-like" or "s-like" shapes.
        """
        if self.shape() in ("flat", "w-like", "s-like"):
            return None
        c = self.path.centroid()
        return (1000 * Particle(c.x, c.y).perpend_dist(self.path,
                                                       posloc=self.posloc) /
                self.path.area())

    def curvature_dev_from_straight(self):
        """ Return a measure of path curvature based on the deviation of
            the path from a straight line; defined as the normalized
            difference in length between path and the straight line between 
            the end nodes of path. Return value is in the range [0,1[ where a  
            lower value corresponds to a flatter path.
        """
        l = geometry.SegmentedPath([self.path[0], self.path[-1]])
        return 1 - l.length() / self.path.length()

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
        self.use_random = False
        self.use_grid = False
        self.stop_requested = False
# end of class OptionData


class ProfileError(exceptions.Exception):
    def __init__(self, profile, msg):
        self.args = (profile, msg + ".")


def profile_warning(profile, msg):
    """ Issue a warning
    """
    sys.stdout.write("Warning: %s.\n" % msg)
    profile.warnflag = True      


def profile_message(msg):
    """ Show a message
    """
    sys.stdout.write("%s.\n" % msg)