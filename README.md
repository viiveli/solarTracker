# SolarTracker
## A bit useless contraption, but hey...
Vaguely engineered autonomous photovoltaic energy harvester running on ESP32 devkit board and micropython. Device uses solar panels to charge a supercapacitor module and once the voltage is high enough the "brain" will boot up and align the solar panels with the brightest source of light ...usually the sun. The device can rotate 360 degrees horizontally and roughly 110 degrees vertically. Average power production level can be monitored and axes controlled through a web UI.

All structural parts including the gears and the custom PCB were designed in Fusion 360. Parts were lasercut at [lasercutstudio.com](https://www.lasercutstudio.com/) from 3mm plywood, custom PCB was ordered from [jlcpcb.com](https://jlcpcb.com). Cheap 112x84mm/6V/200mA solar cells and a supercapacitor module were leftovers from previous projects and horizontal/vertical axes are rotated with two 28BYJ-48 stepper motors controlled with ULN2003 motor drivers.

~~Each solar panel is~~ Due to a PCB design mistake four out of five solar panels (omitting the middle one) are monitored with an ADC pin fed by a simple voltage divider. Divider resistors total at around 12kOhm:s per panel, maybe a bit too little but that's a combination I had lying around. (10k + 2k, giving a convenient 0...1V range for the ADC:s with 6V panel output) If each panel is pushing the specified 6V:s there is a total current of around 2.5mA:s wasted straight to the ground, making around 0.25% of the total maximum capacity. Resistor tolerances seemed to be all over the place so this is far from exact. Later tests showed that with minimal load these panels can actually push up to 8V:s in direct sunshine.

There is an option for a regulator IC on the PCB but these solar panels have such a low output so after few tests decided not to use one... kinda sketchy but I only had 7805:s at hand and those need at least 7V input voltage to function correctly. And since there is no way to tell the absolute position of stepper motors there are two limit switches telling the brain to stop vertical rotation if either one is triggered. The panel alignment begins only if power production level is above the threshold of 70% and once the power drops below 70% the device enters "hibernation" and tries to level the panel array.

<p align="center">
<i>Renderings of original design</i><br>
<img src="img\solartracker_rend1.png" width=320>
<img src="img\solartracker_rend2.png" width=320><br><br>
<i>Actual device</i><br>
<img src="img\solartracker_pic1.jpg" width=320>
<img src="img\solartracker_pic2.jpg" width=320>
<img src="img\solartracker_pic3.jpg" width=320><br><br>
<i>The device stands and rotates on a concentric "hub" without any bearings</i><br>
<img src="img\solartracker_pic4.jpg" height=320><br><br>
<i>Web UI with power level & controls</i><br>
<img src="img\solartracker_webui.png" width=320>
</p>

### Design flaws and other whoopsies
* Hole diameters for some screws were kinda messed up because I did not take into account the lasers 0.3mm kerf width - managed to replace M3:s with M4:s so not a big issue
* Did not pay enough attention to ESP32 specs when designing the PCB so the middle solar panel level can not be monitored and one spare I/O pin does not work. Luckily this was not a fatal mistake
* After initial testing four shader plates had to be added around the middle solar panel to amplify voltage differences between panels
* Solar panels are a bit too weak for this design. Anything less than direct sunlight means that the device will not work - I've seen similar sized panels with 12V output
* Vertical axis really does not need to flip from side to another. Makes things unnecessarily complicated. Had to scratch my head a bit because the horizontal alignment has to invert when the vertical axis flips from side to side

### Fun project nevertheless!
These days it seems like you can order pretty much everything by mail, including custom parts and PCB:s - and this is what I wanted to test with this project. Of course this way the price per part is kinda high and of course it would be nice to have your own 3d printer or a CNC router but it's not necessary if you want to build something. Those tools can be really expensive, and they require space and maintenance too. Sure it takes a bit more time this way and if you make a design mistake you can't just instantly make a replacement, but let's not be in hurry all the time

-w