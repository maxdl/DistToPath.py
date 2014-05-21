from __future__ import with_statement
#import sys
import os.path
import time
from classes import *
import geometry
from fileIO import *
import version
import stringconv

    
#
# Functions
#

def evaluatedProfileLi(profileli):
    """ Return a list of synapses which were parsed and evaluated 
        w/o errors so far  
    """ 
    return [pro for pro in profileli if not pro.errflag]


def saveOutput(profileli, opt):
    """ Save a summary of results of evaluated profiles
    """
    def m(x, pixelwidth):
        return geometry.toMetricUnits(x, pixelwidth)

    def m2(x, pixelwidth): 
        return geometry.toMetricUnits(x, pixelwidth**2)  # for area units...
    
    def m_inv(x):
        try:
            return 1 / m(1 / x)
        except (TypeError, ZeroDivisionError):
            return None

    def writeSessionSummary():
        with FileWriter("session.summary", opt) as f:
            f.writerow(["%s version:" % version.title,
                       "%s (Last modified %s %s, %s)"
                       % ((version.version,) + version.date)])
            f.writerow(["Number of evaluated profiles:", len(eval_proli)])
            if err_fli:
                f.writerow(["Number of non-evaluated profiles:", len(err_fli)])
            f.writerow(["Metric unit:", eval_proli[0].metric_unit])
            f.writerow(["Spatial resolution:", opt.spatial_resolution, eval_proli[0].metric_unit])
            if clean_fli:
                f.writerow(["Input files processed cleanly:"])
                f.writerows([[fn] for fn in clean_fli])
            if nop_fli:
                f.writerow(["Input files processed but which generated no "
                            "particle distances:"])
                f.writerows([[fn] for fn in nop_fli])
            if warn_fli:
                f.writerow(["Input files processed but which generated "
                            "warnings (see log for details):"]) 
                f.writerows([[fn] for fn in warn_fli])
            if err_fli:
                f.writerow(["Input files not processed or not included in "
                            "summary (see log for details):"])
                f.writerows([[fn] for fn in err_fli])


    def writeProfileSummary():
        with FileWriter("profile summary", opt) as f:
            f.writerow(["Path length",                       
                        "Particles (total)",
                        "Positive particles",
                        "Positive shell particles",
                        "Negative shell particles",
                        "Shell particles positive or within %s %s of path"
                            % (opt.spatial_resolution, eval_proli[0].metric_unit),        
                        "Particles within %s %s of path" 
                            % (opt.spatial_resolution, eval_proli[0].metric_unit),
                        "Profile ID",
                        "Input file",
                        "Comment"])
            f.writerows([[m(pro.path.length(), pro.pixelwidth), 
                          len(pro.pli),
                          len([p for p in pro.pli if p.distToPath >= 0]),
                          len([p for p in pro.pli if p.isWithinShell 
                                                   and p.distToPath >= 0]),
                          len([p for p in pro.pli if p.isWithinShell 
                                                   and p.distToPath < 0]),
                          len([p for p in pro.pli 
                               if (p.isWithinShell 
                                   and (p.distToPath >= 0))
                                or p.isAssociatedWithPath]),
                          len([p for p in pro.pli if p.isAssociatedWithPath]),
                          pro.ID,
                          os.path.basename(pro.inputfn),
                          pro.comment] 
                          for pro in eval_proli])
                      
    def writeParticleSummary():
        with FileWriter("particle.summary", opt) as f:
            f.writerow(["Particle number (as appearing in input file)", 
                        "Perpendicular distance to path", 
                        "Lateral distance to center of path", 
                        "Lateral distance to center of path"
                            " / path radius",
                        "Particle associated w/ path",
                        #"Nearest neighbour",
                        "Path length",
                        "Profile ID",
                        "Input file",
                        "Comment"])
            f.writerows([[n+1, 
                          m(p.distToPath, pro.pixelwidth), 
                          m(p.lateralDistPath, pro.pixelwidth), 
                          p.lateralDistPath / (pro.path.length() / 2),
                          stringconv.yes_or_no(p.isAssociatedWithPath),
                          #tostr(m(p.nearestNeighbour, s.pixelwidth), 2),
                          m(pro.path.length(), pro.pixelwidth),
                          pro.ID,
                          os.path.basename(pro.inputfn), 
                          pro.comment]
                          for pro in eval_proli for n, p in enumerate(pro.pli)])
            
    def writeRandomSummary():
        with FileWriter("random.summary", opt) as f:
            f.writerow(["Point number (as appearing in input file)", 
                        "Perpendicular distance to path", 
                        "Lateral distance to center of path", 
                        "Lateral distance to center of path"
                            " / path radius",
                        "Particle associated w/ path",
                        #"Nearest neighbour",
                        "Path length",
                        "Profile ID",
                        "Input file",
                        "Comment"])
            f.writerows([[n+1, 
                          m(p.distToPath, pro.pixelwidth), 
                          m(p.lateralDistPath, pro.pixelwidth), 
                          p.lateralDistPath / (pro.path.length() / 2),
                          stringconv.yes_or_no(p.isAssociatedWithPath),
                          #tostr(m(p.nearestNeighbour, s.pixelwidth), 2),
                          m(pro.path.length(), pro.pixelwidth),
                          pro.ID,
                          os.path.basename(pro.inputfn), 
                          pro.comment]
                          for pro in eval_proli for n, p in enumerate(pro.randomli)])

    def writeGridSummary():
        with FileWriter("grid.summary", opt) as f:
            f.writerow(["Point number (as appearing in input file)", 
                        "Perpendicular distance to path", 
                        "Lateral distance to center of path", 
                        "Lateral distance to center of path"
                            " / path radius",
                        "Particle associated w/ path",
                        #"Nearest neighbour",
                        "Path length",
                        "Profile ID",
                        "Input file",
                        "Comment"])
            f.writerows([[n+1, 
                          m(p.distToPath, pro.pixelwidth), 
                          m(p.lateralDistPath, pro.pixelwidth), 
                          p.lateralDistPath / (pro.path.length() / 2),
                          stringconv.yes_or_no(p.isAssociatedWithPath),
                          #tostr(m(p.nearestNeighbour, s.pixelwidth), 2),
                          m(pro.path.length(), pro.pixelwidth),
                          pro.ID,
                          os.path.basename(pro.inputfn), 
                          pro.comment]
                          for pro in eval_proli for n, p in enumerate(pro.gridli)])
            
    def writeInterparticleSummary():
        with FileWriter("interparticle.summary", opt) as f:        
            f.writerow(["P1", "P2", "Distance", "Input file"])
            for pro in eval_proli:
                n = 0
                for n1 in range(0, len(pro.pli)):
                    for n2 in range(n1+1, len(pro.pli)):
                        #if (pro.pli[n1].isAssociatedWithPath and
                        #    pro.pli[n2].isAssociatedWithPath):
                        f.writerow([n1+1, n2+1, 
                                    m(pro.pli[n1].dist(pro.pli[n2]), 
                                      pro.pixelwidth),
                                    os.path.basename(pro.inputfn)])
                        n += 1
            
    sys.stdout.write("\nSaving summaries...\n")
    opt.save_result = {'any_saved': False, 'any_err': False}
    eval_proli = [pro for pro in profileli if not pro.errflag]
    clean_fli = [pro.inputfn for pro in profileli if not (pro.errflag or pro.warnflag)]
    warn_fli = [pro.inputfn for pro in profileli if pro.warnflag]
    err_fli = [pro.inputfn for pro in profileli if pro.errflag]
    nop_fli = [pro.inputfn for pro in profileli if not pro.pli]
    if opt.output_file_format == 'excel':
        import xls
    elif opt.output_file_format == 'csv':
        csv_format = { 'dialect' : 'excel', 'lineterminator' : '\n'}
        if opt.csv_delimiter == 'tab':
            csv_format['delimiter'] = '\t'                
    if opt.outputs['session summary']: writeSessionSummary()
    if opt.outputs['profile summary']: writeProfileSummary()
    if opt.outputs['particle summary']: writeParticleSummary()
    if opt.outputs['random summary'] and opt.useRandom: writeRandomSummary()
    if opt.gridSummary and opt.useGrid: writeGridSummary()
    if opt.interparticleSummary: writeInterparticleSummary()

    
def showOptions(opt):
    sys.stdout.write("%s version: %s (Last modified %s %s, %s)\n" 
                      % ((version.title, version.version) + version.date))                           
    sys.stdout.write("Output file format: %s\n" % opt.output_file_format)
    sys.stdout.write("Suffix of output files: %s\n"
                     % opt.output_filename_suffix)
    sys.stdout.write("Output directory: %s\n" % opt.output_dir)
    sys.stdout.write("Spatial resolution: %d\n" % opt.spatial_resolution)
    sys.stdout.write("Shell width: %d metric units\n" % opt.shell_width)    



def getOutputFormat(opt):
    if opt.output_file_format == 'excel':
        try:
            import xls
        except ImportError:
            sys.stdout.write("Unable to write Excel files: resorting to csv "
                             "format.\n")
            opt.output_file_format = "csv"
    if opt.output_file_format == 'csv':
        opt.output_filename_ext = ".csv"
        opt.csv_format = { 'dialect' : 'excel', 'lineterminator' : '\n',
                       'encoding': sys.getfilesystemencoding() }
        if opt.csv_delimiter == 'tab':
            opt.csv_format['delimiter'] = '\t'
    if opt.output_filename_date_suffix:
        from datetime import date
        opt.output_filename_suffix = "." + date.today().isoformat()
    if opt.output_filename_other_suffix != '':
        opt.output_filename_suffix += "." + opt.output_filename_other_suffix
      
def mainProc(parent, opt):
    """ Process profile data files
    """
    
    def removeDuplicateFilenames(fli):
        """ Remove duplicate filenames in input file list
        """
        for f in fli:
            if fli.count(f) > 1:
                sys.stdout.write("Duplicate input filename %s:\n   => " 
                                 "removing first occurrence in list\n" % f)
                fli.remove(f)    
    
    if not opt.input_file_list:
        sys.stdout.write("No input files.\n")
        return 0                 
    i, n = 0, 0
    profileli = []
    sys.stdout.write("--- Session started %s local time ---\n" 
                      % time.ctime())
    removeDuplicateFilenames(opt.input_file_list)
    #getOutputDir(opt)
    getOutputFormat(opt)
    showOptions(opt)
    while True:
        if i < len(opt.input_file_list):
            inputfn = opt.input_file_list[i]
            i += 1
        else: 
            sys.stdout.write("\nNo more input files...\n")
            break
        parent.process_queue.put(("new_file", inputfn))
        profileli.append(ProfileData(inputfn, opt))
        profileli[-1].process(opt)
        if opt.stop_requested:
            sys.stdout.write("\n--- Session aborted by user %s local time ---\n" 
                             % time.ctime())
            return 3                    
        if not profileli[-1].errflag:
            n += 1
            if profileli[-1].warnflag:
                sys.stdout.write("Warning(s) found while processing "
                                 "input file.\n")
                continue
        else:
            sys.stdout.write("Error(s) found while processing input file =>\n"
                             "  => No distances could be determined.\n")
            continue
    # no more input files
    errfli = [pro.inputfn for pro in profileli if pro.errflag]
    warnfli = [pro.inputfn for pro in profileli if pro.warnflag]
    if errfli:
        sys.stdout.write("\n%s input %s generated one or more "
                        "errors:\n"
                         % (stringconv.plurality("This", len(errfli)),
                            stringconv.plurality("file", len(errfli))))
        sys.stdout.write("%s\n" % "\n".join([fn for fn in errfli]))
    if warnfli:
        sys.stdout.write("\n%s input %s generated one or more warnings:\n"
                         % (stringconv.plurality("This", len(warnfli)),
                            stringconv.plurality("file", len(warnfli))))
        sys.stdout.write("%s\n" % "\n".join([fn for fn in warnfli]))
    if n > 0:
        parent.process_queue.put(("saving_summaries", ""))
        saveOutput(profileli, opt)        
    else:
        sys.stdout.write("\nNo files processed.\n")
    sys.stdout.write("--- Session ended %s local time ---\n" % time.ctime())
    parent.process_queue.put(("done", ""))
    if errfli: 
        return 0
    elif warnfli: 
        return 2
    else: 
        return 1
# End of main.py
