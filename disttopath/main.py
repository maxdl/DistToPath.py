# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
import os.path
import time
from core import *
import geometry
import file_io
import version
import stringconv

    
#
# Functions
#

def evaluated_profile_li(profileli):
    """ Return a list of synapses which were parsed and evaluated 
        w/o errors so far  
    """ 
    return [pro for pro in profileli if not pro.errflag]


def save_output(profileli, opt):
    """ Save a summary of results of evaluated profiles
    """
    def m(x, pixelwidth):
        return geometry.to_metric_units(x, pixelwidth)

    def write_session_summary():
        with file_io.FileWriter("session.summary", opt) as f:
            f.writerow(["%s version:" % version.title,
                       "%s (Last modified %s %s, %s)"
                        % ((version.version,) + version.date)])
            f.writerow(["Number of evaluated profiles:", len(eval_proli)])
            if err_fli:
                f.writerow(["Number of non-evaluated profiles:", len(err_fli)])
            f.writerow(["Metric unit:", eval_proli[0].metric_unit])
            f.writerow(["Spatial resolution:", opt.spatial_resolution, 
                        eval_proli[0].metric_unit])
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

    def write_profile_summary():
        with file_io.FileWriter("profile summary", opt) as f:
            f.writerow(["Path length",                       
                        "Particles (total)",
                        "Positive particles",
                        "Positive shell particles",
                        "Negative shell particles",
                        "Shell particles positive or within %s %s of path"
                        % (opt.spatial_resolution,
                           eval_proli[0].metric_unit),
                        "Particles within %s %s of path" 
                        % (opt.spatial_resolution,
                           eval_proli[0].metric_unit),
                        "Profile id",
                        "Input file",
                        "Comment"])
            f.writerows([[m(pro.path.length(), pro.pixelwidth), 
                          len(pro.pli),
                          len([p for p in pro.pli if p.dist_to_path >= 0]),
                          len([p for p in pro.pli if p.is_within_shell
                               and p.dist_to_path >= 0]),
                          len([p for p in pro.pli if p.is_within_shell 
                               and p.dist_to_path < 0]),
                          len([p for p in pro.pli 
                               if (p.is_within_shell 
                                   and (p.dist_to_path >= 0))
                               or p.is_assoc_with_path]),
                          len([p for p in pro.pli if p.is_assoc_with_path]),
                          pro.id,
                          os.path.basename(pro.inputfn),
                          pro.comment] for pro in eval_proli])
                      
    def write_particle_summary():
        with file_io.FileWriter("particle.summary", opt) as f:
            f.writerow(["Particle number (as appearing in input file)", 
                        "Perpendicular distance to path", 
                        "Lateral distance to center of path", 
                        "Lateral distance to center of path / path radius",
                        "Particle associated w/ path",
                        # "Nearest neighbour",
                        "Path length",
                        "Profile id",
                        "Input file",
                        "Comment"])
            f.writerows([[n + 1,
                          m(p.dist_to_path, pro.pixelwidth), 
                          m(p.lateral_dist_path, pro.pixelwidth), 
                          p.lateral_dist_path / (pro.path.length() / 2),
                          stringconv.yes_or_no(p.is_assoc_with_path),
                          # tostr(m(p.nearest_neighbour, s.pixelwidth), 2),
                          m(pro.path.length(), pro.pixelwidth),
                          pro.id,
                          os.path.basename(pro.inputfn), 
                          pro.comment] for pro in eval_proli for n, p in
                         enumerate(pro.pli)])
            
    def write_random_summary():
        with file_io.FileWriter("random.summary", opt) as f:
            f.writerow(["Point number (as appearing in input file)", 
                        "Perpendicular distance to path", 
                        "Lateral distance to center of path", 
                        "Lateral distance to center of path"
                            " / path radius",
                        "Particle associated w/ path",
                        # "Nearest neighbour",
                        "Path length",
                        "Profile id",
                        "Input file",
                        "Comment"])
            f.writerows([[n + 1,
                          m(p.dist_to_path, pro.pixelwidth), 
                          m(p.lateral_dist_path, pro.pixelwidth), 
                          p.lateral_dist_path / (pro.path.length() / 2),
                          stringconv.yes_or_no(p.is_assoc_with_path),
                          # tostr(m(p.nearest_neighbour, s.pixelwidth), 2),
                          m(pro.path.length(), pro.pixelwidth),
                          pro.id,
                          os.path.basename(pro.inputfn), 
                          pro.comment]
                          for pro in eval_proli
                          for n, p in enumerate(pro.randomli)])

    def write_grid_summary():
        with file_io.FileWriter("grid.summary", opt) as f:
            f.writerow(["Point number (as appearing in input file)", 
                        "Perpendicular distance to path", 
                        "Lateral distance to center of path", 
                        "Lateral distance to center of path / path radius",
                        "Particle associated w/ path",
                        # "Nearest neighbour",
                        "Path length",
                        "Profile id",
                        "Input file",
                        "Comment"])
            f.writerows([[n + 1, 
                          m(p.dist_to_path, pro.pixelwidth), 
                          m(p.lateral_dist_path, pro.pixelwidth), 
                          p.lateral_dist_path / (pro.path.length() / 2),
                          stringconv.yes_or_no(p.is_assoc_with_path),
                          # tostr(m(p.nearest_neighbour, s.pixelwidth), 2),
                          m(pro.path.length(), pro.pixelwidth),
                          pro.id,
                          os.path.basename(pro.inputfn), 
                          pro.comment]
                         for pro in eval_proli
                         for n, p in enumerate(pro.gridli)])
            
    def write_interparticle_summary():
        with file_io.FileWriter("interparticle.summary", opt) as f:        
            f.writerow(["P1", "P2", "Distance", "Input file"])
            for pro in eval_proli:
                n = 0
                for n1 in range(0, len(pro.pli)):
                    for n2 in range(n1 + 1, len(pro.pli)):
                        # if (pro.pli[n1].is_assoc_with_path and
                        #     pro.pli[n2].is_assoc_with_path):
                        f.writerow([n1 + 1, n2 + 1,
                                    m(pro.pli[n1].dist(pro.pli[n2]),
                                      pro.pixelwidth),
                                    os.path.basename(pro.inputfn)])
                        n += 1
            
    sys.stdout.write("\nSaving summaries...\n")
    opt.save_result = {'any_saved': False, 'any_err': False}
    eval_proli = [profile for profile in profileli if not profile.errflag]
    clean_fli = [profile.inputfn for profile in profileli
                 if not (profile.errflag or profile.warnflag)]
    warn_fli = [profile.inputfn for profile in profileli if profile.warnflag]
    err_fli = [profile.inputfn for profile in profileli if profile.errflag]
    nop_fli = [profile.inputfn for profile in profileli if not profile.pli]
    if opt.outputs['session summary']:
        write_session_summary()
    if opt.outputs['profile summary']:
        write_profile_summary()
    if opt.outputs['particle summary']:
        write_particle_summary()
    if opt.outputs['random summary'] and opt.use_random:
        write_random_summary()
    if opt.gridSummary and opt.use_grid:
        write_grid_summary()
    if opt.interparticleSummary:
        write_interparticle_summary()


def reset_options(opt):
    """ Deletes certain options that should always be set anew for each run
        (each time the "Start" button is pressed)
    """
    if hasattr(opt, "metric_unit"):
        delattr(opt, "metric_unit")
    if hasattr(opt, "use_polarity"):
        delattr(opt, "use_polarity")
    if hasattr(opt, "use_grid"):
        delattr(opt, "use_grid")
    if hasattr(opt, "use_random"):
        delattr(opt, "use_random")


def show_options(opt):
    sys.stdout.write("{} version: {} (Last modified {} {}, {})\n".format(
                     version.title, version.version, *version.date))
    sys.stdout.write("Output file format: %s\n" % opt.output_file_format)
    sys.stdout.write("Suffix of output files: %s\n"
                     % opt.output_filename_suffix)
    sys.stdout.write("Output directory: %s\n" % opt.output_dir)
    sys.stdout.write("Spatial resolution: %d\n" % opt.spatial_resolution)
    sys.stdout.write("Shell width: %d metric units\n" % opt.shell_width)    


def get_output_format(opt):
    if opt.output_file_format == 'excel':
        import imp
        try:
            imp.find_module("pyExcelerator")
        except ImportError:
            sys.stdout.write("Unable to write Excel files: resorting to csv "
                             "format.\n")
            opt.output_file_format = "csv"
    if opt.output_file_format == 'csv':
        opt.output_filename_ext = ".csv"
        opt.csv_format = {'dialect': 'excel', 'lineterminator': '\n',
                          'encoding': sys.getfilesystemencoding()}
        if opt.csv_delimiter == 'tab':
            opt.csv_format['delimiter'] = '\t'
    if opt.output_filename_date_suffix:
        from datetime import date
        opt.output_filename_suffix = "." + date.today().isoformat()
    if opt.output_filename_other_suffix != '':
        opt.output_filename_suffix += "." + opt.output_filename_other_suffix
      

def main_proc(parent):
    """ Process profile data files
    """
    opt = parent.opt
    if not opt.input_file_list:
        sys.stdout.write("No input files.\n")
        return 0                 
    i, n = 0, 0
    profileli = []
    sys.stdout.write("--- Session started %s local time ---\n" % time.ctime())
    # Remove duplicate filenames
    for f in opt.input_file_list:
        if opt.input_file_list.count(f) > 1:
            sys.stdout.write("Duplicate input filename %s:\n   => "
                             "removing first occurrence in list\n" % f)
            opt.input_file_list.remove(f)
    get_output_format(opt)
    reset_options(opt)
    show_options(opt)
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
        sys.stdout.write("\n%s input %s generated one or more errors:\n"
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
        save_output(profileli, opt)        
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
