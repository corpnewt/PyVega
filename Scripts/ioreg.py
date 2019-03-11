import os, sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))))
import run

class IOReg:
    def __init__(self):
        self.ioreg = {}
        self.r = run.Run()

    def get_devices(self,dev_list = None, **kwargs):
        force = kwargs.get("force",False)
        plane = kwargs.get("plane","IOService")
        # Iterate looking for our device(s)
        # returns a list of devices@addr
        if dev_list == None:
            return []
        if not isinstance(dev_list, list):
            dev_list = [dev_list]
        if force or not self.ioreg.get(plane,None):
            self.ioreg[plane] = self.r.run({"args":["ioreg", "-l", "-p", plane, "-w0"]})[0].split("\n")
        dev = []
        for line in self.ioreg[plane]:
            if any(x for x in dev_list if x in line) and "+-o" in line:
                dev.append(line.split("+-o ")[1].split("  ")[0])
        return dev

    def get_device_info(self, dev_search = None, **kwargs):
        force = kwargs.get("force",False)
        plane = kwargs.get("plane","IOService")
        isclass = kwargs.get("isclass",False)
        # Returns a list of all matched classes and their properties
        if not dev_search:
            return []
        if force or not self.ioreg.get(plane,None):
            self.ioreg[plane] = self.r.run({"args":["ioreg", "-l", "-p", plane, "-w0"]})[0].split("\n")
        dev = []
        primed = False
        current = None
        search = dev_search if not isclass else "<class " + dev_search
        for line in self.ioreg[plane]:
            if not primed and not search in line:
                continue
            if not primed:
                primed = True
                current = {"name":dev_search,"parts":{}}
                continue
            # Primed, but not our device
            if "+-o" in line:
                # Past our prime - see if we have a current, save
                # it to the list, and clear it
                primed = False
                if current:
                    dev.append(current)
                    current = None
                continue
            # Primed, not class, not next device - must be info
            try:
                name = line.split(" = ")[0].split('"')[1]
                current["parts"][name] = line.split(" = ")[1]
            except Exception as e:
                pass
        return dev

    def get_acpi_path(self, device, **kwargs):
        force = kwargs.get("force",False)
        plane = kwargs.get("plane","IOService")
        if not device:
            return ""
        if force or not self.ioreg.get(plane,None):
            self.ioreg[plane] = self.r.run({"args":["ioreg", "-l", "-p", plane, "-w0"]})[0].split("\n")
        path = []
        found = False
        # First we find our device if it exists - and save each step
        for x in self.ioreg[plane]:
            if "<class " in x:
                path.append(x)
                if device in x:
                    found = True
                    break
        if not found:
            return ""
        # Got a path - walk backward
        out = []
        prefix = None
        # Work in reverse to find our path
        for x in path[::-1]:
            parts = x.split("+-o ")
            if prefix == None or len(parts[0]) < len(prefix):
                # Path length changed, must be parent?
                item = parts[1].split("  ")[0]
                prefix = parts[0]
                out.append(item)
        # Reverse the path
        out = out[::-1]
        return "/".join(out)

    def get_device_path(self, device, **kwargs):
        path = self.get_acpi_path(device, **kwargs)
        if not path:
            return ""
        out = path.split("/")
        dev_path = ""
        for x in out:
            if not "@" in x:
                continue
            if not len(dev_path):
                # First entry
                dev_path = "PciRoot(0x{})".format(x.split("@")[1])
            else:
                # Not first
                outs = x.split("@")[1].split(",")
                d = outs[0]
                f = 0 if len(outs) == 1 else outs[1]
                dev_path += "/Pci(0x{},0x{})".format(d,f)
        return dev_path