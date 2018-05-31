import itertools
import os.path
import time
from .core import *
from . import geometry
from . import file_io
from . import version
from . import stringconv


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

    def na(x):
        if x in (None, -1):
            return "N/A"
        else:
            return x

    def write_session_summary():
        if not opt.outputs['session summary']:
            return
        with file_io.FileWriter("session.summary", opt) as f:
            f.writerow(["%s version:" % version.title,
                       "%s (Last modified %s %s, %s)" % ((version.version,) + version.date)])
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
                f.writerow(["Input files processed but which generated no particle distances:"])
                f.writerows([[fn] for fn in nop_fli])
            if warn_fli:
                f.writerow(["Input files processed but which generated warnings "
                            "(see log for details):"])
                f.writerows([[fn] for fn in warn_fli])
            if err_fli:
                f.writerow(["Input files not processed or not included in summary "
                            "(see log for details):"])
                f.writerows([[fn] for fn in err_fli])

    def write_profile_summary():
        if not opt.outputs['profile summary']:
            return
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
                               or p.is_associated_with_path]),
                          len([p for p in pro.pli if p.is_associated_with_path]),
                          pro.id,
                          os.path.basename(pro.inputfn),
                          pro.comment] for pro in eval_proli])
                      
    def write_point_summary(ptype):
        if ptype == 'particle' and opt.outputs['particle summary']:
            pli = 'pli'
            pstr = 'particle'
        elif ptype == 'random' and opt.outputs['random summary'] and opt.use_random:
            pli = 'randomli'
            pstr = 'point'
        else:
            return
        with file_io.FileWriter("%s.summary" % ptype, opt) as f:
            f.writerow(["%s number (as appearing in input file)" % pstr.capitalize(),
                        "Perpendicular distance to path", 
                        "Lateral distance to center of path", 
                        "Lateral distance to center of path / path radius",
                        "Particle associated w/ path",
                        "Path length",
                        "Profile id",
                        "Input file",
                        "Comment"])
            f.writerows([[n + 1,
                          m(p.dist_to_path, pro.pixelwidth), 
                          m(p.lateral_dist_path, pro.pixelwidth), 
                          p.lateral_dist_path / (pro.path.length() / 2),
                          stringconv.yes_or_no(p.is_associated_with_path),
                          m(pro.path.length(), pro.pixelwidth),
                          pro.id,
                          os.path.basename(pro.inputfn), 
                          pro.comment] for pro in eval_proli for n, p in
                         enumerate(pro.__dict__[pli])])

    def write_cluster_summary():
        if not opt.determine_clusters:
            return
        with file_io.FileWriter("cluster.summary", opt) as f:
            f.writerow(["Cluster number",
                        "Number of particles in cluster",
                        "Distance of centroid to path",
                        "Distance to nearest cluster along path "
                        "Path length",
                        "Profile ID",
                        "Input file",
                        "Comment"])
            f.writerows([[n + 1,
                          len(c),
                          m(c.dist_to_path, pro.pixelwidth),
                          m(na(c.dist_to_nearest_cluster), pro.pixelwidth),
                          pro.id,
                          os.path.basename(pro.inputfn),
                          pro.comment] for pro in eval_proli for n, c in
                         enumerate(pro.clusterli)])

    def write_interpoint_summaries():
        if not opt.determine_interpoint_dists:
            return
        ip_rels = dict([(key, val)
                        for key, val in opt.interpoint_relations.items()
                        if val and 'simulated' not in key])
        if not opt.use_random:
            for key, val in opt.interpoint_relations.items():
                if 'random' in key and val:
                    del ip_rels[key]
        if (len(ip_rels) == 0 or not
                (opt.interpoint_shortest_dist or opt.interpoint_lateral_dist)):
            return
        table = []
        if opt.interpoint_dist_mode == 'all':
            s = "all distances"
        else:
            s = "nearest neighbour distances"
        table.append(["Mode: " + s])
        headerli = list(ip_rels.keys())
        prefixli = []
        for key, val in ip_rels.items():
            prefix = key[0] + key[key.index('- ') + 2] + '_'
            prefixli.append(prefix)
        if opt.interpoint_shortest_dist and opt.interpoint_lateral_dist:
            headerli.extend(headerli)
            prefixli.extend([t + 'lat' for t in prefixli])
        topheaderli = []
        if opt.interpoint_shortest_dist:
            topheaderli.append("Shortest distances")
            if opt.interpoint_lateral_dist:
                topheaderli.extend([""] * (len(ip_rels) - 1))
        if opt.interpoint_lateral_dist:
            topheaderli.append("Lateral distances along path")
        table.extend([topheaderli, headerli])
        cols = [[] for _ in prefixli]
        for pro in eval_proli:
            for n, li in enumerate([pro.__dict__[prefix + 'distli'] for prefix in prefixli]):
                cols[n].extend([m(e, pro.pixelwidth) for e in li])
        # transpose cols and append to table
        table.extend(list(itertools.zip_longest(*cols, fillvalue="")))
        with file_io.FileWriter("interpoint.distances", opt) as f:
            f.writerows(table)

    def write_mc_dist_to_path():
        if not opt.run_monte_carlo:
            return
        table = [["Run %d" % (n + 1)
                  for n in range(0, opt.monte_carlo_runs)]]
        for pro in eval_proli:
            table.extend(itertools.zip_longest(*[[m(p.dist_to_path, pro.pixelwidth)
                                                  for p in li['pli']] for li in pro.mcli]))
        with file_io.FileWriter("simulated.path.distances", opt) as f:
            f.writerows(table)

    def write_mc_ip_dists(dist_type):
        if not (opt.run_monte_carlo and opt.determine_interpoint_dists):
            return
        for ip_type in [key for key, val in opt.interpoint_relations.items()
                        if 'simulated' in key and val]:
            if ((dist_type == 'shortest' and not opt.interpoint_shortest_dist) or
                    (dist_type == 'lateral' and not opt.interpoint_lateral_dist)):
                return
            if dist_type == 'lateral':
                short_dist_type = 'lat'
            else:
                short_dist_type = ''
            table = [["Run %d" % (n + 1) for n in range(0, opt.monte_carlo_runs)]]
            for pro in eval_proli:
                table.extend(itertools.zip_longest(*[m(p, pro.pixelwidth)
                                                     for li in pro.mcli
                                                     for p in li[ip_type]["%sdist"
                                                                          % short_dist_type]]))
            with file_io.FileWriter("%s.interpoint.%s.distance.summary"
                                    % (ip_type.replace(" ", ""), dist_type), opt) as f:
                f.writerows(table)

    def write_mc_cluster_summary():
        if not (opt.determine_clusters and opt.run_monte_carlo):
            return
        table = [["N particles in cluster", "Run",
                  "Distance of centroid to path",
                  "Distance to nearest cluster along path "
                  "membrane",
                  "Profile ID",
                  "Input file",
                  "Comment"]]
        for pro in eval_proli:
            for n in range(0, opt.monte_carlo_runs):
                for c in pro.mcli[n]['clusterli']:
                    table.append([len(c), n + 1,
                                  m(c.dist_to_path, pro.pixelwidth),
                                  m(na(c.dist_to_nearest_cluster),
                                    pro.pixelwidth),
                                  pro.id,
                                  os.path.basename(pro.inputfn),
                                  pro.comment])
        with file_io.FileWriter("simulated.cluster.summary", opt) as f:
            f.writerows(table)

    sys.stdout.write("\nSaving summaries...\n")
    opt.save_result = {'any_saved': False, 'any_err': False}
    eval_proli = [profile for profile in profileli if not profile.errflag]
    clean_fli = [profile.inputfn for profile in profileli
                 if not (profile.errflag or profile.warnflag)]
    warn_fli = [profile.inputfn for profile in profileli if profile.warnflag]
    err_fli = [profile.inputfn for profile in profileli if profile.errflag]
    nop_fli = [profile.inputfn for profile in profileli if not profile.pli]
    write_session_summary()
    write_profile_summary()
    write_point_summary('particle')
    write_point_summary('random')
    write_interpoint_summaries()
    write_cluster_summary()
    write_mc_dist_to_path()
    write_mc_ip_dists('shortest')
    write_mc_ip_dists('lateral')
    write_mc_cluster_summary()
    if opt.save_result['any_err']:
        sys.stdout.write("Note: One or more summaries could not be saved.\n")
    if opt.save_result['any_saved']:
        sys.stdout.write("Done.\n")
    else:
        sys.stdout.write("No summaries saved.\n")

def reset_options(opt):
    """ Deletes certain options that should always be set anew for each run
        (each time the "Start" button is pressed)
    """
    for optstr in ('metric_unit', 'use_polarity', 'use_grid', 'use_random'):
        if hasattr(opt, optstr):
            delattr(opt, optstr)


def show_options(opt):
    sys.stdout.write("{} version: {} (Last modified {} {}, {})\n".format(
                     version.title, version.version, *version.date))
    sys.stdout.write("Output file format: %s\n" % opt.output_file_format)
    sys.stdout.write("Suffix of output files: %s\n" % opt.output_filename_suffix)
    sys.stdout.write("Output directory: %s\n" % opt.output_dir)
    sys.stdout.write("Spatial resolution: %d\n" % opt.spatial_resolution)
    sys.stdout.write("Shell width: %d metric units\n" % opt.shell_width)
    sys.stdout.write("Interpoint distances calculated: %s\n"
                     % stringconv.yes_or_no(opt.determine_interpoint_dists))
    if opt.determine_interpoint_dists:
        sys.stdout.write("Interpoint distance mode: %s\n" % opt.interpoint_dist_mode.capitalize())
        sys.stdout.write("Shortest interpoint distances: %s\n"
                         % stringconv.yes_or_no(opt.interpoint_shortest_dist))
        sys.stdout.write("Lateral interpoint distances: %s\n"
                         % stringconv.yes_or_no(opt.interpoint_lateral_dist))
    sys.stdout.write("Monte Carlo simulations performed: %s\n"
                     % stringconv.yes_or_no(opt.run_monte_carlo))
    if opt.run_monte_carlo:
        sys.stdout.write("Number of Monte Carlo runs: %d\n" % opt.monte_carlo_runs)
        sys.stdout.write("Monte Carlo simulation window: %s\n" % opt.monte_carlo_simulation_window)
    sys.stdout.write("Clusters determined: %s\n" % stringconv.yes_or_no(opt.determine_clusters))
    if opt.determine_clusters:
        sys.stdout.write("Within-cluster distance: %d\n" % opt.within_cluster_dist)


def get_output_format(opt):
    if opt.output_file_format == 'excel':
        try:
            import openpyxl
        except ImportError:
            sys.stdout.write("Unable to write Excel files: resorting to csv format.\n")
            opt.output_file_format = 'csv'
    if opt.output_file_format == 'csv':
        opt.output_filename_ext = '.csv'
        opt.csv_format = {'dialect': 'excel', 'lineterminator': '\n'}
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
            sys.stdout.write("Duplicate input filename %s:\n   => removing first occurrence in "
                             "list\n" % f)
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
        parent.process_queue.put(('new_file', inputfn))
        profileli.append(Profile(inputfn, opt))
        profileli[-1].process(opt)
        if opt.stop_requested:
            sys.stdout.write("\n--- Session aborted by user %s local time ---\n" 
                             % time.ctime())
            return 3                    
        if not profileli[-1].errflag:
            n += 1
            if profileli[-1].warnflag:
                sys.stdout.write("Warning(s) found while processing input file.\n")
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
