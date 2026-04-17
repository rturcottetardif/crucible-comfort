# Creating Crucible-Comfort

## Forking crucible-lite into your own standalone repo
1. Clone the original repo

```
git clone git@github.com:drsiyaoshao-sudo/crucible-lite.git
cd crucible-lite
```

2. Remove the link to the original repo

```
git remote remove origin
```

3. Create your own new repo on GitHub and push to it

```
gh repo create crucible-comfort --private --source=. --push
Replace crucible-comfort with your project name
```

Use `--public` instead of `--private` if you want it public
This creates the repo on GitHub and pushes your code in one step

4. Verify

```
git remote -v
```
Should show origin pointing to your new repo.

5. (Optional) Rename the local folder to match

```
cd ..
mv crucible-lite crucible-comfort
cd crucible-comfort
```

6. Start developing

```
git checkout -b my-feature
# make changes
git add .
git commit -m "my changes"
git push -u origin my-feature
```

You now have a fully independent repo with crucible-lite's scaffolding as the starting point, no fork relationship on GitHub, and can make it private.

## Installing according to `/ONBOARDING.md`

**What is missing in the instructions or in the repo:**

- Adding a `.gitignore` and adding `.venv` in `.gitignore`
```
touch .gitignore
```

Then open .gitignore in your editor and add common Python entries:

```
.venv/
__pycache__/
*.pyc
.env
.DS_Store
```
Commit it:

```
git add .gitignore
git commit -m "Add .gitignore"
git push
```

- Creation of a venv. WHICH PYTHON VERSION?
```
python -m venv .venv
source .venv/bin/activate
```

-- Step ask for which renode, pio and ninja, but doesn't state to install them. 
For Mac user:
```
brew install ninja
brew install platformio
brew tap renode/tap
brew install renode/tap/renode
```

---> Installation surprisingly took me 5 hours (from the cloning to the installation of all requirements). To be honest my computer package are a mess. I used Claude to help me through some cleaning and installation <---

## Primitives. Physics first. 
I think in the `README.md` the first principle should be **Physics first** and not signal first (for me the signal is what you get after the sensors).

Ok let's think about primitive. It's a bit foreign for my brain. 

What do I want:
- I want a HVAC sensor kit that I can **retrofit** on old Heatpump (the external part).
- It should inform me of when the **filters have to be changed** (this would save money of maintenance company, instead of going every X months, they can go when needed instead.) You could think about something similar for car or trucks oil changes. 
- I want the kit to also **detect breakage** (ideally before it break, but at least when it does break).
- I want the kit to calculate the **power consumption** (detect anomaly in power consumption)

So instinctively I would design a kit with:
- **Power clamp** around the power supply cable to monitor the power consumption
- **Microphone or contact microphone** to detect weird sound (mainly from the fan), microphone could possibly detect leak (unlikely)
- **IMU** to detect abnormal vibration (clogged, leaking pipe?, bearing wear)
- **Temparture sensor**.... Not sure if that' very useful...
- I cannot use any pressure differential or temperature differential because it's a non-invasive retrofit kit.

How to translate that in primitive??

Let's try...
Primitives
- Power consumption
- Stability in time of the system (head)
- Rotational velocity of the fan or noise of the system in time (which one is the primitive, vitesse of the fan i guess, noise is second order effect)
- The condensation on the pipe with respect to the outside temperature

----
# Day 2

We are simplifying crucible-comfort. The task is mono. We want to be able to detect when the filters have to be changed. 

So we need to know when the air does flow doesn't flow well anymore through the filter. The primitive is called **Porosity Ratio**.

Let see if the pipeline can get it from engineering specs (engineering language)


`claude`

In the Claude CLI
read CLAUDE.md ---> that makes sure that Claude adheres to the constitution
/spec







