# Rolling Pool Editor 使用說明

## 程式說明

Rolling Pool Editor 需搭配 **Smithbox** 使用。程式輸出的檔案為與 Smithbox 相容的 CSV，可匯入指定參數欄位，建立可供遊戲使用的 `regulation.bin`。

## CSV 匯入流程

### 1. 建立 Smithbox 專案

建立 Smithbox 專案時，可使用已修改完成的 **Grand Only Base** 作為 `regulation.bin`。其基礎版本為 **Regulation Ver. 1.03.5**，並包含以下調整：

- 抽獎池只會抽到 **Grand Scene**。
- 下修 Grand Scene 的購買價格。
- 約每賣出 7 顆所產生的價差，可額外購買 1 顆。
- 在改善抽取體驗的同時，兼顧 **Murk** 的數量平衡。

### 2. 選擇參數表

在 Smithbox 的 **Param Editor** 中選擇：

```text
AttachEffectTableParam
```

### 3. 匯入 CSV

依序開啟：

```text
Tool → Data Transfer → Import CSV → From File...
```

在 **From File...** 的子選單中選擇 **Specific Field**，接著會顯示可匯入的欄位清單。下列兩個欄位都必須使用 CSV 覆蓋：

```text
chanceWeight
chanceWeight_dlc
```

Smithbox 一次只能選擇並匯入一個欄位，因此必須執行兩次匯入：

1. 選擇 `chanceWeight`，待檔案選取對話窗開啟後，選取 Rolling Pool Editor 輸出的 CSV。
2. 再次開啟相同選單，選擇 `chanceWeight_dlc`，並在檔案選取對話窗中選取同一份 CSV。

完成以上兩次操作後，兩個欄位才算全部覆蓋完成。

> [!WARNING]
> 請勿選擇 **All Field**。使用 All Field 匯入可能會錯誤覆寫其他欄位，導致參數資料異常。

### 4. 載入 Mod

完成匯入並儲存 Smithbox 專案後，修改過的 `regulation.bin` 即可作為 Mod，透過 **Mod Engine 3（ME3）** 載入遊戲。

> [!CAUTION]
> 建議且應使用 **Mod Engine 3（ME3）** 管理及載入 Mod，避免直接修改遊戲的原始檔案。
>
> 雖然你也可以直接覆蓋遊戲原始的 `regulation.bin`，並於之後透過遊戲平台的「驗證檔案完整性」功能將其還原，但若忘記還原修改過的檔案，可能會導致帳號遭到封鎖（BAN）。請自行承擔直接覆蓋原始遊戲檔案的風險。
