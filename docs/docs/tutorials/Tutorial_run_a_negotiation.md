# Running a negotiation

NegMAS has several built-in negotiation `Mechanisms`, negotiation agents (`Negotiators`), and `UtilityFunctions`. You can use these to run negotiations as follows.

Imagine a buyer and a seller negotiating over the price of a single object. First, we make an issue "price" with 50 discrete values. Note here, it is possible to create multiple issues, but we will not include that here. If you are interested, see the [NegMAS documentation](https://negmas.readthedocs.io/en/latest/tutorials/01.running_simple_negotiation.html) for a tutorial.


```python
from negmas import (
    make_issue,
    SAOMechanism,
   TimeBasedConcedingNegotiator,
)
from anl.anl2024.negotiators import Boulware, Conceder, RVFitter
from negmas.preferences import LinearAdditiveUtilityFunction as UFun
from negmas.preferences.value_fun import IdentityFun, AffineFun
import matplotlib.pyplot as plt


# create negotiation agenda (issues)
issues = [
    make_issue(name="price", values=50),
]

# create the mechanism
session = SAOMechanism(issues=issues, n_steps=20)
```

The negotiation protocol in NegMAS is handled by a `Mechanism` object. Here we instantiate a`SAOMechanism` which implements the [Stacked Alternating Offers Protocol](https://ii.tudelft.nl/~catholijn/publications/sites/default/files/Aydogan2017_Chapter_AlternatingOffersProtocolsForM.pdf). In this protocol, negotiators exchange offers until an offer is accepted by all negotiators (in this case 2), a negotiators leaves the table ending the negotiation or a time-out condition is met. In the example above, we use a limit on the number of rounds of `20` (a step of a mechanism is an executed round).

Next, we define the utilities of the seller and the buyer. The utility function of the seller is defined by the ```
IdentityFun```  which means that the higher the price, the higher the utility function. The buyer's utility function is reversed. The last two lines make sure that utility is scaled between 0 and 1.


```python
seller_utility = UFun(
    values=[IdentityFun()],
    outcome_space=session.outcome_space,
)

buyer_utility = UFun(
    values=[AffineFun(slope=-1)],
    outcome_space=session.outcome_space,
)

seller_utility = seller_utility.normalize()
buyer_utility = buyer_utility.normalize()

```

Then we add two agents with a boulware strategy. The negotiation ends with status overview. For example, you can see if the negotiation timed-out, what agreement was found, and how long the negotiation took. Moreover, we output the full negotiation history. For a more visual representation, we can plot the session. This shows the bidding curve, but also the proximity to e.g. the Nash point.


```python
# create and add agent A and B
session.add(Boulware(name="seller"), ufun=seller_utility)
session.add(Boulware(name="buyer"), ufun=buyer_utility)

# run the negotiation and show the results
print(session.run())

# negotiation history
for i, _ in enumerate(session.history):
    print(f"{i:03}: {_.new_offers}")  # the first line gives the offer of the seller and the buyer  in the first round

session.plot(ylimits=(0.0, 1.01), show_reserved=False, mark_max_welfare_points=False)
plt.show()


```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">SAOState</span><span style="font-weight: bold">(</span>
    <span style="color: #808000; text-decoration-color: #808000">running</span>=<span style="color: #ff0000; text-decoration-color: #ff0000; font-style: italic">False</span>,
    <span style="color: #808000; text-decoration-color: #808000">waiting</span>=<span style="color: #ff0000; text-decoration-color: #ff0000; font-style: italic">False</span>,
    <span style="color: #808000; text-decoration-color: #808000">started</span>=<span style="color: #00ff00; text-decoration-color: #00ff00; font-style: italic">True</span>,
    <span style="color: #808000; text-decoration-color: #808000">step</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">18</span>,
    <span style="color: #808000; text-decoration-color: #808000">time</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.006180799915455282</span>,
    <span style="color: #808000; text-decoration-color: #808000">relative_time</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.9047619047619048</span>,
    <span style="color: #808000; text-decoration-color: #808000">broken</span>=<span style="color: #ff0000; text-decoration-color: #ff0000; font-style: italic">False</span>,
    <span style="color: #808000; text-decoration-color: #808000">timedout</span>=<span style="color: #ff0000; text-decoration-color: #ff0000; font-style: italic">False</span>,
    <span style="color: #808000; text-decoration-color: #808000">agreement</span>=<span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">23</span>,<span style="font-weight: bold">)</span>,
    <span style="color: #808000; text-decoration-color: #808000">results</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
    <span style="color: #808000; text-decoration-color: #808000">n_negotiators</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2</span>,
    <span style="color: #808000; text-decoration-color: #808000">has_error</span>=<span style="color: #ff0000; text-decoration-color: #ff0000; font-style: italic">False</span>,
    <span style="color: #808000; text-decoration-color: #808000">error_details</span>=<span style="color: #008000; text-decoration-color: #008000">''</span>,
    <span style="color: #808000; text-decoration-color: #808000">threads</span>=<span style="font-weight: bold">{}</span>,
    <span style="color: #808000; text-decoration-color: #808000">last_thread</span>=<span style="color: #008000; text-decoration-color: #008000">''</span>,
    <span style="color: #808000; text-decoration-color: #808000">current_offer</span>=<span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">23</span>,<span style="font-weight: bold">)</span>,
    <span style="color: #808000; text-decoration-color: #808000">current_proposer</span>=<span style="color: #008000; text-decoration-color: #008000">'seller-69622b52-7474-4027-bdda-e2928ad686cf'</span>,
    <span style="color: #808000; text-decoration-color: #808000">current_proposer_agent</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
    <span style="color: #808000; text-decoration-color: #808000">n_acceptances</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2</span>,
    <span style="color: #808000; text-decoration-color: #808000">new_offers</span>=<span style="font-weight: bold">[(</span><span style="color: #008000; text-decoration-color: #008000">'seller-69622b52-7474-4027-bdda-e2928ad686cf'</span>, <span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">23</span>,<span style="font-weight: bold">))]</span>,
    <span style="color: #808000; text-decoration-color: #808000">new_offerer_agents</span>=<span style="font-weight: bold">[</span><span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span><span style="font-weight: bold">]</span>,
    <span style="color: #808000; text-decoration-color: #808000">last_negotiator</span>=<span style="color: #008000; text-decoration-color: #008000">'seller'</span>
<span style="font-weight: bold">)</span>
</pre>




    
![png](Tutorial_run_a_negotiation_files/Tutorial_run_a_negotiation_6_1.png)
    

[Download Notebook](/anl/tutorials/notebooks/Tutorial_run_a_negotiation.ipynb)
