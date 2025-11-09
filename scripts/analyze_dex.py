"""
Analyze classes.dex to find HR-related commands and protocol details
"""
import sys

try:
    from androguard.core.dex import DEX
except ImportError:
    print("Installing androguard...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "androguard"])
    from androguard.core.dex import DEX


def analyze_dex(dex_path):
    """Analyze DEX file for Chileaf protocol information"""
    
    print("=" * 80)
    print("Analyzing classes.dex for HR history support")
    print("=" * 80)
    
    # Load DEX file
    print(f"\n[1/5] Loading DEX file: {dex_path}")
    with open(dex_path, 'rb') as f:
        dex_data = f.read()
    d = DEX(dex_data)
    
    classes = list(d.get_classes())
    print(f"  ✓ Loaded {len(classes)} classes")
    
    # Find relevant classes
    print("\n[2/5] Searching for Chileaf-related classes...")
    chileaf_classes = []
    hr_classes = []
    
    for cls in classes:
        class_name = cls.get_name()
        
        # Look for Chileaf package classes
        if 'chileaf' in class_name.lower() or 'wear' in class_name.lower():
            chileaf_classes.append(cls)
            
        # Look for HR-related classes
        if 'heart' in class_name.lower() or 'hr' in class_name.lower():
            hr_classes.append(cls)
    
    print(f"  ✓ Found {len(chileaf_classes)} Chileaf classes")
    print(f"  ✓ Found {len(hr_classes)} HR-related classes")
    
    # List key classes
    print("\n[3/5] Key classes found:")
    for cls in chileaf_classes[:20]:  # Show first 20
        print(f"  - {cls.get_name()}")
    
    # Search for command constants
    print("\n[4/5] Searching for command byte constants (0x21, 0x22, 33, 34)...")
    command_references = []
    
    for cls in chileaf_classes:
        class_name = cls.get_name()
        
        # Check static fields for command constants
        for field in cls.get_fields():
            field_name = field.get_name()
            
            # Look for command-related field names
            if any(keyword in field_name.lower() for keyword in ['cmd', 'command', 'hr', 'heart']):
                try:
                    init_value = field.get_init_value()
                    if init_value:
                        value = init_value.get_value()
                        if value in [0x21, 0x22, 33, 34, 0x24, 0x25, 36, 37]:
                            command_references.append({
                                'class': class_name,
                                'field': field_name,
                                'value': value
                            })
                            print(f"  ✓ Found: {class_name} -> {field_name} = {value} (0x{value:02X})")
                except:
                    pass
        
        # Check methods for byte array literals containing 0x21, 0x22
        for method in cls.get_methods():
            method_name = method.get_name()
            
            # Look for relevant method names
            if any(keyword in method_name.lower() for keyword in ['hr', 'heart', 'history', 'record', 'gethistory']):
                print(f"\n  📍 Method: {class_name}.{method_name}")
                
                try:
                    # Get method bytecode
                    code = method.get_code()
                    if code:
                        # Get bytecode
                        bc = code.get_bc()
                        
                        # Look for const instructions with our values
                        for instr in bc.get_instructions():
                            instr_name = instr.get_name()
                            if 'const' in instr_name:
                                try:
                                    # Get the literal value
                                    output = instr.get_output()
                                    # Check if output contains our target values
                                    if any(str(v) in output for v in [0x21, 0x22, 33, 34, 0x24, 0x25, 36, 37]):
                                        print(f"    → Instruction: {output}")
                                        # Try to extract the value
                                        for v in [0x21, 0x22, 33, 34, 0x24, 0x25, 36, 37]:
                                            if str(v) in output:
                                                command_references.append({
                                                    'class': class_name,
                                                    'method': method_name,
                                                    'value': v
                                                })
                                                break
                                except:
                                    pass
                except Exception as e:
                    pass
    
    # Search for specific method implementations
    print("\n[5/5] Looking for WearManager sendCommand method...")
    for cls in chileaf_classes:
        if 'WearManager' in cls.get_name():
            print(f"\n  📦 Class: {cls.get_name()}")
            
            for method in cls.get_methods():
                method_name = method.get_name()
                
                if 'sendCommand' in method_name or 'getHistoryOfHR' in method_name:
                    print(f"    ✓ Method: {method_name}")
                    print(f"      Descriptor: {method.get_descriptor()}")
                    
                    # Try to show method code
                    try:
                        code = method.get_code()
                        if code:
                            print(f"      Registers: {code.get_registers_size()}")
                    except:
                        pass
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Chileaf classes: {len(chileaf_classes)}")
    print(f"Total HR classes: {len(hr_classes)}")
    print(f"Command references found: {len(command_references)}")
    
    if command_references:
        print("\nCommand byte references:")
        for ref in command_references[:10]:  # Show first 10
            print(f"  - {ref}")
    else:
        print("\n⚠ No direct command byte references found in bytecode")
        print("  This is normal - commands may be in parent SDK classes or obfuscated")
    
    print("\n" + "=" * 80)
    print("To decompile full source code, use:")
    print("  jadx -d output_folder classes.dex")
    print("=" * 80)


if __name__ == "__main__":
    dex_file = r"c:\Users\UserDemo\Documents\VScode\python_bt\python_bt\documentation\classes.dex"
    analyze_dex(dex_file)
