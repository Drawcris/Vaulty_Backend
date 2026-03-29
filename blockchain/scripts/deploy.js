const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("Rozpoczynam wdrażanie kontraktu VaultyAccess...");

  const VaultyAccess = await hre.ethers.getContractFactory("VaultyAccess");
  const contract = await VaultyAccess.deploy();

  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`VaultyAccess zostal wdrożony pod adresem: ${address}`);

  // Zapisz adres do pliku, aby backend i frontend mogły go łatwo odczytać
  const deploymentInfo = {
    address: address,
    network: hre.network.name,
    deployedAt: new Date().toISOString()
  };

  const deploymentPath = path.join(__dirname, "..", "deployment.json");
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`Informacje o wdrożeniu zapisano w: ${deploymentPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
