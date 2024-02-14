Changelog
=========

0.1.9 (2024.02.14)
------------------

- Adding divide-the-pies scenarios
- Adding workflow to test on negmas master
- Tutorial and docs update
- Update faq

0.1.8 (2023.12.31)
------------------

* bugfix in visualizer initial tournament list
* Correcting auto pushing to PyPi

0.1.7 (2023.12.31)
------------------

* Adding simple dockerfile
* Adding --port, --address to anlv show. You can now set the port and address of the visualizer
* Visualizer parses folders recursively
* minor: faster saving of figs
* Adding mkdocs to dev requirements
* Removing NaiveTitForTat from the default set of competitors
* Improving tutorial

0.1.6 (2023.12.27)
------------------

* Improved visualizer
    - Adding filtering by scenario or strategy to the main view.
    - Adding new options to show scenario statistics, scenario x strategy statistics, and cases with no agreements at all.
    - You can show multiple negotiations together
    - You can show the descriptive statistics of any metric according to strategy or scenario
    - More plotting options for metrics

* Improved CLI
    - Adding the ability to pass parameters to competitors in the CLI.
    - Removing NaiveTitForTat from the default set of competitors
    - Making small tournaments even smaller

* New and improved strategies
    - Adding RVFitter strategy which showcases simple implementation of curve fitting for reserved value estimation and using logging.
    - Adding more comments to NashSeeker strategy
    - Simplified implementation of MiCRO
    - Adding a simple test for MiCRO
    - Avoid failure when Nash cannot be found in NashSeeker

* Migrating to NegMAS 0.10.11. Needed for logging (and 0.10.10 is needed for self.oppponent_ufun)

0.1.5 (2023.12.24)
------------------

* Changing default order of agents
* Adding a basic visualizer
* Adding make-scenarios to the CLI
* Passing opponent ufun in the private info
* Separating implementation of builtin agents
* requiring NegMAS 0.10.9

0.1.4 (2023.12.24)
------------------

* Retrying scenario generation if it failed
* Defaulting to no plotting in windows

0.1.3 (2023.12.23)
------------------

* Defaulting to no-plotting on windows to avoid an error caused by tkinter
* Retry scenario generation on failure. This is useful for piece-wise linear which will fail (by design) if n_pareto happened to be less than n_segments + 1

0.1.2 (2023.12.18)
------------------

* Adding better scenario generation and supporting mixtures of zero-sum, monotonic and general scenarios.
* Requiring negmas 0.10.8

0.1.2 (2023.12.11)
------------------

* Controlling log path in anl2024_tournament() through the added base_path argument

0.1.1 (2023.12.09)
------------------
* Added anl cli for running tournaments.
* Added the ability to hide or show type names during negotiations
* Corrected a bug in importing unique_name
* Now requires negmas 0.10.6

0.1.0 (2023.11.30)
------------------

* Adding ANL 2024 placeholder
