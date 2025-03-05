"""
Module for template initialization and project structure handling
"""

def initialize_blank_template():
    """Initialize a blank template for an AELF contract."""
    components = {}
    
    # Initialize main contract file
    components["main_contract"] = {
        "content": """using AElf.Sdk.CSharp;
using Google.Protobuf.WellKnownTypes;

namespace AElf.Contracts.HelloWorld
{
    /// <summary>
    /// The HelloWorld Smart Contract.
    /// NOTE: This is just a starter template. These basic methods should be REPLACED with appropriate 
    /// functionality based on your specific dApp requirements.
    /// </summary>
    public class HelloWorld : HelloWorldContainer.HelloWorldBase
    {
        /// <summary>
        /// Initialize the contract.
        /// </summary>
        /// <param name="input">Empty message as the input.</param>
        /// <returns>Empty message as the output.</returns>
        public override Empty Initialize(Empty input)
        {
            Assert(!State.Initialized.Value, "Already initialized.");
            State.Initialized.Value = true;
            return new Empty();
        }

        /// <summary>
        /// Updates the message stored in the contract state.
        /// NOTE: This is a placeholder method and should be replaced with appropriate dApp functionality.
        /// </summary>
        /// <param name="input">The new message to store.</param>
        /// <returns>An empty object.</returns>
        public override Empty Update(StringValue input)
        {
            Assert(State.Initialized.Value, "Not initialized.");
            State.Message.Value = input.Value;
            
            // Emit an event to notify clients
            Context.Fire(new UpdatedMessage
            {
                Value = input.Value
            });
            
            return new Empty();
        }

        /// <summary>
        /// Reads the message stored in the contract state.
        /// NOTE: This is a placeholder method and should be replaced with appropriate dApp functionality.
        /// </summary>
        /// <param name="input">Empty message as the input.</param>
        /// <returns>The current message stored in the contract state.</returns>
        public override StringValue Read(Empty input)
        {
            return new StringValue { Value = State.Message.Value };
        }
    }
}""",
        "file_type": "csharp",
        "path": "src/HelloWorld.cs",
        "contract_name": "HelloWorld"
    }
    
    # Initialize state file
    components["state"] = {
        "content": """using AElf.Sdk.CSharp.State;

namespace AElf.Contracts.HelloWorld
{
    /// <summary>
    /// The state class for the HelloWorld contract.
    /// This class should be REPLACED with state variables appropriate for your specific dApp requirements.
    /// </summary>
    public class HelloWorldState : ContractState
    {
        /// <summary>
        /// A boolean state to track if the contract has been initialized.
        /// </summary>
        public BoolState Initialized { get; set; }
        
        /// <summary>
        /// A state property that holds a string value.
        /// This is a placeholder and should be replaced with appropriate state variables.
        /// </summary>
        public StringState Message { get; set; }
    }
}""",
        "file_type": "csharp",
        "path": "src/HelloWorldState.cs",
        "contract_name": "HelloWorld"
    }
    
    # Initialize contract references file
    components["reference"] = {
        "content": """using AElf.Contracts.MultiToken;

namespace AElf.Contracts.HelloWorld
{
    /// <summary>
    /// The contract reference class for the HelloWorld contract.
    /// This class should be updated with references to other contracts that your contract needs to interact with.
    /// </summary>
    public partial class HelloWorldState
    {
        /// <summary>
        /// Reference to the Token Contract for handling token-related operations.
        /// </summary>
        internal TokenContractContainer.TokenContractReferenceState TokenContract { get; set; }
    }
}""",
        "file_type": "csharp",
        "path": "src/ContractReferences.cs",
        "contract_name": "HelloWorld"
    }
    
    # Initialize proto file
    components["proto"] = {
        "content": """syntax = "proto3";

import "aelf/options.proto";
import "google/protobuf/empty.proto";
import "google/protobuf/wrappers.proto";

option csharp_namespace = "AElf.Contracts.HelloWorld";

service HelloWorld {
    option (aelf.csharp_state) = "AElf.Contracts.HelloWorld.HelloWorldState";
    
    // NOTE: These methods are placeholders and should be replaced with appropriate methods for your dApp
    
    // Initialize the contract
    rpc Initialize (google.protobuf.Empty) returns (google.protobuf.Empty) {
    }

    // Update a string value in the contract state
    rpc Update (google.protobuf.StringValue) returns (google.protobuf.Empty) {
    }
    
    // Read the string value from the contract state
    rpc Read (google.protobuf.Empty) returns (google.protobuf.StringValue) {
        option (aelf.is_view) = true;
    }
}

// An event that will be emitted from contract method call
message UpdatedMessage {
    option (aelf.is_event) = true;
    string value = 1;
}""",
        "file_type": "proto",
        "path": "src/Protobuf/contract/hello_world.proto",
        "contract_name": "HelloWorld"
    }
    
    # Initialize csproj file
    components["project"] = {
        "content": """<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <TargetFramework>net8.0</TargetFramework>
        <RootNamespace>AElf.Contracts.HelloWorld</RootNamespace>
        <IsContract>true</IsContract>
        <CheckForOverflowUnderflow>true</CheckForOverflowUnderflow>
        <AssemblyVersion>1.0.0.0</AssemblyVersion>
    </PropertyGroup>
     <PropertyGroup>
        <ObjPath>$(MSBuildProjectDirectory)/$(BaseIntermediateOutputPath)$(Configuration)/$(TargetFramework)/</ObjPath>
    </PropertyGroup>

    <Target Name="ProtoGeneratedRecognition" AfterTargets="CoreCompile">
        <ItemGroup>
            <Compile Include="$(ObjPath)Protobuf/**/*.cs" />
        </ItemGroup>
    </Target>
    <ItemGroup>
         <PackageReference Include="AElf.Sdk.CSharp" Version="1.10.0" />
        <PackageReference Include="AElf.Tools" Version="1.0.2">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
    </ItemGroup>
    <!-- Add additional package references as needed for your specific dApp requirements -->
</Project>""",
        "file_type": "xml",
        "path": "src/HelloWorld.csproj",
        "contract_name": "HelloWorld"
    }
    
    # Initialize metadata for extra files
    components["metadata"] = [
        {
            "content": """syntax = "proto3";

package authority_info;

option csharp_namespace = "AElf.Contracts.HelloWorld";

// The authority info for the contract
message AuthorityInfo {
    // The contract address
    string contract_address = 1;
    // The owner address
    string owner_address = 2;
}""",
            "file_type": "proto",
            "path": "src/Protobuf/message/authority_info.proto",
            "contract_name": "HelloWorld"
        },
        {
            "content": "// ACS12.proto is assumed to be available in the AELF environment",
            "file_type": "proto",
            "path": "src/Protobuf/reference/acs12.proto",
            "contract_name": "HelloWorld"
        }
    ]
    
    return components

def get_contract_tree_structure(contract_name):
    """Return a tree structure of the contract project."""
    contract_name_lower = contract_name.lower()
    
    return f"""{contract_name}-contract/
|_src/
    |_{contract_name}.csproj
    |_{contract_name}.cs
    |_{contract_name}State.cs
    |_Protobuf/
        |_contract/
            |_{contract_name_lower}.proto
        |_reference/
           |_acs12.proto
        |_message/
           |_authority_info.proto"""

